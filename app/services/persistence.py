"""Persistence helpers for raw loads, screening runs, and quality logs."""

from __future__ import annotations

import math
from typing import Any
from uuid import UUID

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.connectors.base import ConnectorResult
from app.core.utils import utc_now
from app.models.base import Base
from app.models.tables import (
    DataQualityIssue,
    RawBlackrockFundRecord,
    RawBlackrockHoldingRecord,
    RawSanctionsRecord,
    RawSourceSnapshot,
    ScreeningMatch,
    ScreeningMatchEvidence,
    ScreeningRun,
)
from app.services.quality import QualityIssue


def _json_safe(value: Any) -> Any:
    """Recursively replace NaN-like values before writing JSON payloads."""

    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def ensure_tables(engine) -> None:
    """Create tables if migrations have not been applied yet."""

    Base.metadata.create_all(bind=engine)


def persist_connector_result(session: Session, result: ConnectorResult) -> RawSourceSnapshot:
    """Persist connector metadata and raw records."""

    snapshot = RawSourceSnapshot(
        source_system=result.source_system,
        dataset_name=result.dataset_name,
        extraction_mode=result.extraction_mode,
        ingestion_ts=result.retrieved_at,
        snapshot_path=str(result.snapshot_path),
        file_hash=result.file_hash,
        row_count=result.row_count,
        source_url=result.source_url,
        source_last_updated=result.source_last_updated,
        source_metadata=result.metadata,
    )
    session.add(snapshot)
    session.flush()

    ingested_at = result.retrieved_at
    if result.source_system in {"UN", "EU", "OFAC"}:
        session.bulk_save_objects(
            [
                RawSanctionsRecord(
                    snapshot_id=snapshot.snapshot_id,
                    source_system=result.source_system,
                    source_record_id=str(record.get("source_record_id") or record.get("uid") or ""),
                    source_url=record.get("source_url") or result.source_url,
                    source_last_updated=result.source_last_updated,
                    raw_payload=_json_safe(record),
                    ingested_at=ingested_at,
                )
                for record in result.records
            ]
        )
    elif result.dataset_name == "funds":
        session.bulk_save_objects(
            [
                RawBlackrockFundRecord(
                    snapshot_id=snapshot.snapshot_id,
                    source_record_id=str(record.get("fund_id") or record.get("isin") or ""),
                    source_url=record.get("blackrock_url") or result.source_url,
                    raw_payload=_json_safe(record),
                    ingested_at=ingested_at,
                )
                for record in result.records
            ]
        )
    elif result.dataset_name == "holdings":
        session.bulk_save_objects(
            [
                RawBlackrockHoldingRecord(
                    snapshot_id=snapshot.snapshot_id,
                    source_record_id=str(record.get("holding_id") or record.get("issuer_name") or ""),
                    source_url=record.get("source_url") or result.source_url,
                    raw_payload=_json_safe(record),
                    ingested_at=ingested_at,
                )
                for record in result.records
            ]
        )
    return snapshot


def create_screening_run(session: Session, mode: str) -> ScreeningRun:
    """Insert a new pipeline run."""

    run = ScreeningRun(started_at=utc_now(), status="running", mode=mode)
    session.add(run)
    session.flush()
    return run


def finalize_screening_run(
    session: Session,
    run: ScreeningRun,
    matches_df: pd.DataFrame,
    funds_df: pd.DataFrame,
    holdings_df: pd.DataFrame,
    sanctions_df: pd.DataFrame,
    stale_source_warning_count: int,
) -> ScreeningRun:
    """Update run metrics after screening completes."""

    run.finished_at = utc_now()
    run.status = "completed"
    run.total_funds_screened = int(funds_df["fund_id"].nunique()) if not funds_df.empty else 0
    run.total_holdings_screened = int(holdings_df["holding_id"].nunique()) if not holdings_df.empty else 0
    run.total_sanctions_entities = int(sanctions_df["sanctions_entity_id"].nunique()) if not sanctions_df.empty else 0
    run.candidate_matches_count = int(len(matches_df))
    run.high_match_count = int((matches_df["confidence_band"] == "High").sum()) if not matches_df.empty else 0
    run.medium_match_count = int((matches_df["confidence_band"] == "Medium").sum()) if not matches_df.empty else 0
    run.low_match_count = int((matches_df["confidence_band"] == "Low").sum()) if not matches_df.empty else 0
    run.stale_source_warning_count = stale_source_warning_count
    return run


def replace_screening_results(
    session: Session,
    run_id: UUID,
    matches_df: pd.DataFrame,
    evidence_df: pd.DataFrame,
) -> None:
    """Persist screening matches and evidence for a run."""

    session.execute(delete(ScreeningMatch).where(ScreeningMatch.run_id == run_id))
    if matches_df.empty:
        return

    match_objects: list[ScreeningMatch] = []
    match_id_map: dict[tuple[str, str, str], UUID] = {}
    created_at = utc_now()
    for row in matches_df.to_dict(orient="records"):
        match = ScreeningMatch(
            run_id=run_id,
            fund_id=row["fund_id"],
            holding_id=row["holding_id"],
            sanctions_entity_id=row["sanctions_entity_id"],
            source_system=row["source_system"],
            match_type=row["match_type"],
            raw_score=float(row["raw_score"]),
            confidence_band=row["confidence_band"],
            explanation=row["explanation"],
            review_status=row.get("review_status", "Pending"),
            created_at=created_at,
        )
        match_objects.append(match)
        session.add(match)
        session.flush()
        match_id_map[(match.fund_id, match.holding_id, match.sanctions_entity_id)] = match.match_id

    evidence_objects = []
    for row in evidence_df.to_dict(orient="records"):
        match_id = match_id_map.get((row["fund_id"], row["holding_id"], row["sanctions_entity_id"]))
        if match_id is None:
            continue
        evidence_objects.append(
            ScreeningMatchEvidence(
                match_id=match_id,
                evidence_type=row["evidence_type"],
                evidence_key=row["evidence_key"],
                evidence_value=row["evidence_value"],
                created_at=created_at,
            )
        )
    session.bulk_save_objects(evidence_objects)


def persist_quality_issues(session: Session, run_id: UUID | None, issues: list[QualityIssue]) -> None:
    """Persist data quality issues."""

    if not issues:
        return
    session.bulk_save_objects(
        [
            DataQualityIssue(
                run_id=run_id,
                source_system=issue.source_system,
                check_name=issue.check_name,
                severity=issue.severity,
                status=issue.status,
                issue_message=issue.issue_message,
                affected_count=issue.affected_count,
                observed_value=issue.observed_value,
                created_at=utc_now(),
            )
            for issue in issues
        ]
    )
