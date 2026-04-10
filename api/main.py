"""FastAPI application exposing screening results."""

from __future__ import annotations

from typing import Annotated

import pandas as pd
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db_session

app = FastAPI(
    title="SanctionSight API",
    description="Internal API for a public-data analytical prototype. Candidate matches require human review.",
    version="0.1.0",
)

DbSession = Annotated[Session, Depends(get_db_session)]


def _rows(session: Session, sql: str, params: dict | None = None) -> list[dict]:
    frame = pd.read_sql(text(sql), session.bind, params=params or {})
    return frame.to_dict(orient="records")


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "message": "SanctionSight is a public-data analytical prototype, not compliance tooling.",
    }


@app.get("/runs/latest")
def latest_run(db: DbSession) -> dict:
    rows = _rows(db, "select * from screening_run order by started_at desc limit 1")
    if not rows:
        raise HTTPException(status_code=404, detail="No runs found.")
    return rows[0]


@app.get("/metrics/summary")
def metrics_summary(db: DbSession) -> dict:
    latest = _rows(
        db,
        """
        select *
        from mart_screening_overview
        order by started_at desc
        limit 1
        """,
    )
    freshness = _rows(
        db,
        """
        select source_system, dataset_name, ingestion_ts, source_last_updated, row_count, severity, status
        from mart_pipeline_health
        order by source_system, dataset_name
        """,
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No summary metrics available.")
    return {"latest_run": latest[0], "source_freshness": freshness}


@app.get("/funds")
def funds(
    db: DbSession,
    search: str | None = None,
    limit: int = Query(default=100, le=500),
) -> list[dict]:
    sql = """
    select
        f.fund_id,
        f.fund_name,
        f.asset_class,
        f.domicile,
        coalesce(e.candidate_match_count, 0) as candidate_match_count,
        coalesce(e.high_match_count, 0) as high_match_count,
        coalesce(e.unique_flagged_issuers, 0) as unique_flagged_issuers
    from int_curated_funds f
    left join mart_fund_exposure e
        on f.fund_id = e.fund_id
    where (:search is null or upper(f.fund_name) like upper(:pattern))
    order by candidate_match_count desc, f.fund_name
    limit :limit
    """
    pattern = f"%{search}%" if search else None
    return _rows(db, sql, {"search": search, "pattern": pattern, "limit": limit})


@app.get("/funds/{fund_id}")
def fund_detail(fund_id: str, db: DbSession) -> dict:
    fund_rows = _rows(db, "select * from int_curated_funds where fund_id = :fund_id", {"fund_id": fund_id})
    if not fund_rows:
        raise HTTPException(status_code=404, detail="Fund not found.")
    matches = _rows(
        db,
        """
        select *
        from mart_entity_matches
        where fund_id = :fund_id
        order by raw_score desc
        """,
        {"fund_id": fund_id},
    )
    return {"fund": fund_rows[0], "matches": matches}


@app.get("/matches")
def matches(
    db: DbSession,
    confidence_band: str | None = None,
    source_system: str | None = None,
    search: str | None = None,
    limit: int = Query(default=100, le=500),
) -> list[dict]:
    sql = """
    select *
    from mart_entity_matches
    where (:confidence_band is null or confidence_band = :confidence_band)
      and (:source_system is null or source_system = :source_system)
      and (
            :search is null
            or upper(fund_name) like upper(:pattern)
            or upper(issuer_name) like upper(:pattern)
            or upper(sanctions_name) like upper(:pattern)
      )
    order by raw_score desc
    limit :limit
    """
    pattern = f"%{search}%" if search else None
    return _rows(
        db,
        sql,
        {
            "confidence_band": confidence_band,
            "source_system": source_system,
            "search": search,
            "pattern": pattern,
            "limit": limit,
        },
    )


@app.get("/matches/{match_id}")
def match_detail(match_id: str, db: DbSession) -> dict:
    matches = _rows(
        db,
        "select * from mart_entity_matches where match_id = :match_id",
        {"match_id": match_id},
    )
    if not matches:
        raise HTTPException(status_code=404, detail="Match not found.")
    evidence = _rows(
        db,
        """
        select evidence_type, evidence_key, evidence_value, created_at
        from screening_match_evidence
        where match_id = :match_id
        order by evidence_type, evidence_key
        """,
        {"match_id": match_id},
    )
    return {"match": matches[0], "evidence": evidence}


@app.get("/entities/sanctions")
def sanctions_entities(
    db: DbSession,
    source_system: str | None = None,
    search: str | None = None,
    limit: int = Query(default=100, le=500),
) -> list[dict]:
    sql = """
    select *
    from int_curated_sanctions_entities
    where (:source_system is null or source_system = :source_system)
      and (:search is null or upper(primary_name) like upper(:pattern))
    order by source_system, primary_name
    limit :limit
    """
    pattern = f"%{search}%" if search else None
    return _rows(db, sql, {"source_system": source_system, "search": search, "pattern": pattern, "limit": limit})


@app.get("/entities/holdings")
def holdings_entities(
    db: DbSession,
    fund_id: str | None = None,
    search: str | None = None,
    limit: int = Query(default=100, le=500),
) -> list[dict]:
    sql = """
    select *
    from int_curated_holdings
    where (:fund_id is null or fund_id = :fund_id)
      and (:search is null or upper(issuer_name) like upper(:pattern))
    order by fund_id, issuer_name
    limit :limit
    """
    pattern = f"%{search}%" if search else None
    return _rows(db, sql, {"fund_id": fund_id, "search": search, "pattern": pattern, "limit": limit})


def run() -> None:
    """Run the API using Uvicorn."""

    settings = get_settings()
    uvicorn.run("api.main:app", host=settings.api_host, port=settings.api_port, reload=False)


if __name__ == "__main__":
    run()

