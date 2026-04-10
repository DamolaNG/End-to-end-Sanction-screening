"""Database table definitions."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RawSourceSnapshot(Base):
    """Snapshot metadata for raw source extracts."""

    __tablename__ = "raw_source_snapshot"

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_system: Mapped[str] = mapped_column(String(50), index=True)
    dataset_name: Mapped[str] = mapped_column(String(100))
    extraction_mode: Mapped[str] = mapped_column(String(20))
    ingestion_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    snapshot_path: Mapped[str] = mapped_column(Text())
    file_hash: Mapped[str] = mapped_column(String(128))
    row_count: Mapped[int] = mapped_column(Integer())
    source_url: Mapped[str | None] = mapped_column(Text(), nullable=True)
    source_last_updated: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class RawSanctionsRecord(Base):
    """Raw sanctions records stored as source payloads."""

    __tablename__ = "raw_sanctions_record"

    raw_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("raw_source_snapshot.snapshot_id"), index=True
    )
    source_system: Mapped[str] = mapped_column(String(50), index=True)
    source_record_id: Mapped[str] = mapped_column(String(255), index=True)
    source_url: Mapped[str | None] = mapped_column(Text(), nullable=True)
    source_last_updated: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class RawBlackrockFundRecord(Base):
    """Raw BlackRock fund records."""

    __tablename__ = "raw_blackrock_fund_record"

    raw_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("raw_source_snapshot.snapshot_id"), index=True
    )
    source_record_id: Mapped[str] = mapped_column(String(255), index=True)
    source_url: Mapped[str | None] = mapped_column(Text(), nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class RawBlackrockHoldingRecord(Base):
    """Raw BlackRock holding records."""

    __tablename__ = "raw_blackrock_holding_record"

    raw_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("raw_source_snapshot.snapshot_id"), index=True
    )
    source_record_id: Mapped[str] = mapped_column(String(255), index=True)
    source_url: Mapped[str | None] = mapped_column(Text(), nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class ScreeningRun(Base):
    """Pipeline run metadata and KPIs."""

    __tablename__ = "screening_run"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    mode: Mapped[str] = mapped_column(String(20), default="sample")
    total_funds_screened: Mapped[int] = mapped_column(Integer(), default=0)
    total_holdings_screened: Mapped[int] = mapped_column(Integer(), default=0)
    total_sanctions_entities: Mapped[int] = mapped_column(Integer(), default=0)
    candidate_matches_count: Mapped[int] = mapped_column(Integer(), default=0)
    high_match_count: Mapped[int] = mapped_column(Integer(), default=0)
    medium_match_count: Mapped[int] = mapped_column(Integer(), default=0)
    low_match_count: Mapped[int] = mapped_column(Integer(), default=0)
    stale_source_warning_count: Mapped[int] = mapped_column(Integer(), default=0)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    matches: Mapped[list[ScreeningMatch]] = relationship(back_populates="run")


class ScreeningMatch(Base):
    """Candidate screening match."""

    __tablename__ = "screening_match"

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("screening_run.run_id"), index=True)
    fund_id: Mapped[str] = mapped_column(String(255), index=True)
    holding_id: Mapped[str] = mapped_column(String(255), index=True)
    sanctions_entity_id: Mapped[str] = mapped_column(String(255), index=True)
    source_system: Mapped[str] = mapped_column(String(50), index=True)
    match_type: Mapped[str] = mapped_column(String(50))
    raw_score: Mapped[float] = mapped_column(Float())
    confidence_band: Mapped[str] = mapped_column(String(20), index=True)
    explanation: Mapped[str] = mapped_column(Text())
    review_status: Mapped[str] = mapped_column(String(20), default="Pending")
    reviewer_notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    run: Mapped[ScreeningRun] = relationship(back_populates="matches")
    evidence_rows: Mapped[list[ScreeningMatchEvidence]] = relationship(back_populates="match")


class ScreeningMatchEvidence(Base):
    """Evidence records describing how a match was scored."""

    __tablename__ = "screening_match_evidence"

    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("screening_match.match_id"), index=True)
    evidence_type: Mapped[str] = mapped_column(String(50))
    evidence_key: Mapped[str] = mapped_column(String(100))
    evidence_value: Mapped[str] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    match: Mapped[ScreeningMatch] = relationship(back_populates="evidence_rows")


class DataQualityIssue(Base):
    """Persisted data quality results."""

    __tablename__ = "data_quality_issue"

    issue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    source_system: Mapped[str] = mapped_column(String(50), index=True)
    check_name: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    issue_message: Mapped[str] = mapped_column(Text())
    affected_count: Mapped[int] = mapped_column(Integer(), default=0)
    observed_value: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
