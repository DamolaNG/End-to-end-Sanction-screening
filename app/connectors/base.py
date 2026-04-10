"""Connector abstractions and shared utilities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.utils import utc_now, write_json_snapshot


@dataclass(slots=True)
class ConnectorResult:
    """Structured result from a connector extraction."""

    source_system: str
    dataset_name: str
    extraction_mode: str
    retrieved_at: datetime
    source_url: str | None
    snapshot_path: Path
    file_hash: str
    row_count: int
    source_last_updated: datetime | None
    records: list[dict[str, Any]]
    metadata: dict[str, Any]


class BaseConnector(ABC):
    """Base connector with live/sample fallback behavior."""

    source_system: str
    dataset_name: str
    source_url: str | None = None
    user_agent: str = "SanctionSight/0.1 (+https://github.com/openai)"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.logger = get_logger(self.__class__.__name__)

    def run(self) -> ConnectorResult:
        """Fetch a dataset, preferring sample mode when configured."""

        if self.settings.sample_data_mode:
            records, last_updated, metadata = self.load_sample_records()
            extraction_mode = "sample"
        else:
            if not self.settings.allow_live_fetch:
                records, last_updated, metadata = self.load_sample_records()
                extraction_mode = "fallback_sample"
            else:
                try:
                    records, last_updated, metadata = self.fetch_live_records()
                    extraction_mode = "live"
                except Exception as exc:
                    self.logger.warning(
                        "live_fetch_failed_falling_back_to_sample",
                        source_system=self.source_system,
                        error=str(exc),
                    )
                    records, last_updated, metadata = self.load_sample_records()
                    extraction_mode = "fallback_sample"

        timestamp = utc_now()
        snapshot_dir = self.settings.raw_data_dir / self.source_system
        snapshot_path = snapshot_dir / f"{self.dataset_name}_{timestamp.strftime('%Y%m%dT%H%M%SZ')}.json"
        file_hash = write_json_snapshot(snapshot_path, records)
        result = ConnectorResult(
            source_system=self.source_system,
            dataset_name=self.dataset_name,
            extraction_mode=extraction_mode,
            retrieved_at=timestamp,
            source_url=self.source_url,
            snapshot_path=snapshot_path,
            file_hash=file_hash,
            row_count=len(records),
            source_last_updated=last_updated,
            records=records,
            metadata=metadata,
        )
        self.logger.info(
            "connector_completed",
            source_system=self.source_system,
            dataset_name=self.dataset_name,
            row_count=result.row_count,
            extraction_mode=result.extraction_mode,
            file_hash=result.file_hash,
        )
        return result

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def _download_text(self, url: str, timeout: float = 30.0) -> str:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": self.user_agent},
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def _download_bytes(self, url: str, timeout: float = 30.0) -> bytes:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": self.user_agent},
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.content

    @abstractmethod
    def load_sample_records(self) -> tuple[list[dict[str, Any]], datetime | None, dict[str, Any]]:
        """Return sample records, source timestamp, and metadata."""

    @abstractmethod
    def fetch_live_records(self) -> tuple[list[dict[str, Any]], datetime | None, dict[str, Any]]:
        """Return live records, source timestamp, and metadata."""
