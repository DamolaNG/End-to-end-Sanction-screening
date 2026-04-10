"""Logging setup for structured pipeline output."""

from __future__ import annotations

import logging
import sys

import structlog
from structlog.stdlib import BoundLogger

from app.core.config import get_settings


def configure_logging() -> None:
    """Configure stdlib logging and structlog."""

    settings = get_settings()
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> BoundLogger:
    """Return a named logger."""

    configure_logging()
    return structlog.get_logger(name)
