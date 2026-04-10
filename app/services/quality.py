"""Data quality checks and controls."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd

from app.core.config import Settings, get_settings
from app.core.utils import utc_now
from app.schemas.contracts import fund_contract, holding_contract, sanctions_contract


@dataclass(slots=True)
class QualityIssue:
    """Structured data quality issue."""

    source_system: str
    check_name: str
    severity: str
    status: str
    issue_message: str
    affected_count: int = 0
    observed_value: str | None = None


class QualityChecker:
    """Run lightweight data quality validations."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def validate_sanctions(self, source_system: str, frame: pd.DataFrame) -> list[QualityIssue]:
        issues = self._schema_issues(source_system, "sanctions_contract", sanctions_contract, frame)
        issues.extend(self._duplicate_issue(source_system, frame, ["source_record_id"]))
        return issues

    def validate_funds(self, frame: pd.DataFrame) -> list[QualityIssue]:
        issues = self._schema_issues("BLACKROCK", "fund_contract", fund_contract, frame)
        issues.extend(self._duplicate_issue("BLACKROCK", frame, ["fund_id"]))
        return issues

    def validate_holdings(self, frame: pd.DataFrame) -> list[QualityIssue]:
        issues = self._schema_issues("BLACKROCK", "holding_contract", holding_contract, frame)
        issues.extend(self._duplicate_issue("BLACKROCK", frame, ["holding_id"]))
        if "isin" in frame.columns:
            malformed_isin = frame["isin"].fillna("").astype(str).str.len().gt(0) & frame[
                "isin"
            ].astype(str).str.len().ne(12)
        else:
            malformed_isin = pd.Series([], dtype=bool)
        if not malformed_isin.empty and malformed_isin.any():
            issues.append(
                QualityIssue(
                    source_system="BLACKROCK",
                    check_name="malformed_identifier",
                    severity="warning",
                    status="failed",
                    issue_message="One or more holding ISIN values are malformed.",
                    affected_count=int(malformed_isin.sum()),
                )
            )
        return issues

    def stale_source_issue(
        self, source_system: str, source_last_updated: datetime | None
    ) -> list[QualityIssue]:
        if source_last_updated is None:
            return []
        threshold = utc_now() - timedelta(hours=self.settings.stale_source_hours)
        if source_last_updated < threshold:
            return [
                QualityIssue(
                    source_system=source_system,
                    check_name="stale_source",
                    severity="warning",
                    status="failed",
                    issue_message="Source last updated timestamp is stale.",
                    observed_value=source_last_updated.isoformat(),
                )
            ]
        return []

    @staticmethod
    def _schema_issues(
        source_system: str, check_name: str, contract, frame: pd.DataFrame
    ) -> list[QualityIssue]:
        try:
            contract.validate(frame, lazy=True)
            return []
        except Exception as exc:
            return [
                QualityIssue(
                    source_system=source_system,
                    check_name=check_name,
                    severity="error",
                    status="failed",
                    issue_message=str(exc),
                )
            ]

    @staticmethod
    def _duplicate_issue(
        source_system: str, frame: pd.DataFrame, key_columns: list[str]
    ) -> list[QualityIssue]:
        if any(column not in frame.columns for column in key_columns):
            return []
        duplicates = frame.duplicated(subset=key_columns).sum()
        if duplicates:
            return [
                QualityIssue(
                    source_system=source_system,
                    check_name="duplicate_records",
                    severity="warning",
                    status="failed",
                    issue_message=f"Duplicate records detected on {', '.join(key_columns)}.",
                    affected_count=int(duplicates),
                )
            ]
        return []
