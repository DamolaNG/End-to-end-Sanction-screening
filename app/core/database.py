"""Database engine and session helpers."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Create or reuse the SQLAlchemy engine."""

    global _ENGINE
    if _ENGINE is None:
        settings = get_settings()
        _ENGINE = create_engine(settings.database_url, pool_pre_ping=True)
    return _ENGINE


def get_session_factory() -> sessionmaker[Session]:
    """Create or reuse the SQLAlchemy session factory."""

    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _SESSION_FACTORY


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI session dependency."""

    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context-managed transactional session."""

    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

