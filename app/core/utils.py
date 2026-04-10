"""General utility helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def ensure_directory(path: Path) -> Path:
    """Create a directory if it does not exist."""

    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json_snapshot(path: Path, records: list[dict[str, Any]]) -> str:
    """Write records to a JSON snapshot file and return the SHA256 hash."""

    ensure_directory(path.parent)
    path.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")
    return hash_file(path)


def hash_file(path: Path) -> str:
    """Return a SHA256 hash for a file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()
