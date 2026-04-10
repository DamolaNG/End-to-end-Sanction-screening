"""Streamlit dashboard for SanctionSight."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text

from app.core.database import session_scope

st.set_page_config(page_title="SanctionSight", layout="wide")


@st.cache_data(ttl=60)
def load_data(query: str) -> pd.DataFrame:
    with session_scope() as session:
        return pd.read_sql(text(query), session.bind)


def main() -> None:
    st.title("SanctionSight")
    st.caption(
        "Public-data analytical prototype for sanctions exposure monitoring. "
        "Not legal advice or a replacement for regulated compliance tooling."
    )

    page = st.sidebar.radio(
        "Navigate",
        ["Overview", "Match Explorer", "Fund Exposure View", "Entity Detail View", "Data Quality & Pipeline Health"],
    )

    try:
        overview = load_data("select * from mart_screening_overview order by started_at desc")
        fund_exposure = load_data("select * from mart_fund_exposure order by candidate_match_count desc")
        entity_matches = load_data("select * from mart_entity_matches order by raw_score desc")
        pipeline_health = load_data("select * from mart_pipeline_health order by source_system, dataset_name")
        sanctions_entities = load_data(
            "select * from int_curated_sanctions_entities order by source_system, primary_name"
        )
    except Exception as exc:
        st.error(f"Dashboard query failed. Run the pipeline first. Details: {exc}")
        return

    if overview.empty:
        st.warning("No screening runs found yet. Run the ingestion and screening pipeline to populate the dashboard.")
        return

    latest = overview.iloc[0]
    if page == "Overview":
        render_overview(overview, entity_matches, sanctions_entities, latest)
    elif page == "Match Explorer":
        render_match_explorer(entity_matches)
    elif page == "Fund Exposure View":
        render_fund_exposure(fund_exposure, entity_matches)
    elif page == "Entity Detail View":
        render_entity_detail(sanctions_entities, entity_matches)
    else:
        render_pipeline_health(pipeline_health)


def render_overview(
    overview: pd.DataFrame,
    entity_matches: pd.DataFrame,
    sanctions_entities: pd.DataFrame,
    latest: pd.Series,
) -> None:
    cards = st.columns(7)
    cards[0].metric("Funds Screened", int(latest["total_funds_screened"]))
    cards[1].metric("Holdings Screened", int(latest["total_holdings_screened"]))
    cards[2].metric("Sanctions Entities", int(latest["total_sanctions_entities"]))
    cards[3].metric("Candidate Matches", int(latest["candidate_matches_count"]))
    cards[4].metric("High", int(latest["high_match_count"]))
    cards[5].metric("Medium", int(latest["medium_match_count"]))
    cards[6].metric("Low", int(latest["low_match_count"]))

    left, right = st.columns(2)
    with left:
        trend = overview.copy()
        trend["started_at"] = pd.to_datetime(trend["started_at"])
        st.plotly_chart(
            px.line(trend, x="started_at", y="candidate_matches_count", markers=True, title="Candidate Matches Over Time"),
            use_container_width=True,
        )
        sanctions_by_source = sanctions_entities.groupby("source_system").size().reset_index(name="entity_count")
        st.plotly_chart(
            px.bar(sanctions_by_source, x="source_system", y="entity_count", title="Sanctions Records by Source"),
            use_container_width=True,
        )
    with right:
        st.write(f"Latest run timestamp: `{latest['started_at']}`")
        if not entity_matches.empty:
            score_chart = entity_matches.groupby("confidence_band").size().reset_index(name="match_count")
            st.plotly_chart(
                px.pie(score_chart, names="confidence_band", values="match_count", title="Match Confidence Bands"),
                use_container_width=True,
            )
            asset_mix = entity_matches.groupby("fund_name").size().reset_index(name="match_count")
            st.plotly_chart(
                px.bar(asset_mix.head(10), x="fund_name", y="match_count", title="Top Funds by Candidate Matches"),
                use_container_width=True,
            )


def render_match_explorer(entity_matches: pd.DataFrame) -> None:
    confidence = st.selectbox("Confidence Band", ["All", "High", "Medium", "Low"])
    source = st.selectbox("Sanctions Source", ["All"] + sorted(entity_matches["source_system"].dropna().unique().tolist()))
    search = st.text_input("Search by fund, issuer, or sanctions entity")

    filtered = entity_matches.copy()
    if confidence != "All":
        filtered = filtered[filtered["confidence_band"] == confidence]
    if source != "All":
        filtered = filtered[filtered["source_system"] == source]
    if search:
        pattern = search.upper()
        filtered = filtered[
            filtered["fund_name"].fillna("").str.upper().str.contains(pattern)
            | filtered["issuer_name"].fillna("").str.upper().str.contains(pattern)
            | filtered["sanctions_name"].fillna("").str.upper().str.contains(pattern)
        ]

    st.dataframe(
        filtered[
            [
                "match_id",
                "confidence_band",
                "source_system",
                "fund_name",
                "issuer_name",
                "sanctions_name",
                "raw_score",
                "match_type",
                "explanation",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


def render_fund_exposure(fund_exposure: pd.DataFrame, entity_matches: pd.DataFrame) -> None:
    st.dataframe(fund_exposure, use_container_width=True, hide_index=True)
    fund_choices = fund_exposure["fund_id"].dropna().tolist()
    if not fund_choices:
        return
    selected_fund = st.selectbox("Drill into fund", fund_choices)
    detail = entity_matches[entity_matches["fund_id"] == selected_fund]
    st.subheader("Flagged Holdings")
    st.dataframe(detail, use_container_width=True, hide_index=True)


def render_entity_detail(sanctions_entities: pd.DataFrame, entity_matches: pd.DataFrame) -> None:
    if sanctions_entities.empty:
        st.info("No sanctions entities available.")
        return
    entity_name = st.selectbox("Sanctions Entity", sanctions_entities["primary_name"].tolist())
    entity = sanctions_entities[sanctions_entities["primary_name"] == entity_name].iloc[0]
    st.write(entity.to_dict())
    related_matches = entity_matches[entity_matches["sanctions_entity_id"] == entity["sanctions_entity_id"]]
    st.subheader("Matching Funds and Holdings")
    st.dataframe(related_matches, use_container_width=True, hide_index=True)


def render_pipeline_health(pipeline_health: pd.DataFrame) -> None:
    st.dataframe(pipeline_health, use_container_width=True, hide_index=True)
    if not pipeline_health.empty:
        freshness = pipeline_health[["source_system", "dataset_name", "ingestion_ts", "source_last_updated", "status"]]
        st.dataframe(freshness, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()

