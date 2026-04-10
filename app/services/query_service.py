"""Query helpers shared by the API and dashboard."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session


def fetch_dataframe(session: Session, sql: str, params: dict | None = None) -> pd.DataFrame:
    """Return a DataFrame for an arbitrary SQL query."""

    return pd.read_sql(text(sql), session.bind, params=params or {})


def latest_run_summary(session: Session) -> dict:
    """Return the latest screening run summary."""

    frame = fetch_dataframe(
        session,
        """
        select *
        from screening_run
        order by started_at desc
        limit 1
        """,
    )
    return frame.iloc[0].to_dict() if not frame.empty else {}
