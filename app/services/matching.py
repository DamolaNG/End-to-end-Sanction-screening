"""Fuzzy and rule-based sanctions screening engine."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import pandas as pd
from rapidfuzz import fuzz

from app.core.config import Settings, get_settings
from app.services.normalization import expand_aliases, normalize_identifier, normalize_name

IDENTIFIER_FIELDS = ["isin", "cusip", "sedol", "ticker"]


@dataclass(slots=True)
class MatchResultBundle:
    """Container for match and evidence dataframes."""

    matches: pd.DataFrame
    evidence: pd.DataFrame


class ScreeningEngine:
    """Screen curated holdings against curated sanctions entities."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def screen(
        self,
        run_id: UUID,
        funds_df: pd.DataFrame,
        holdings_df: pd.DataFrame,
        sanctions_df: pd.DataFrame,
    ) -> MatchResultBundle:
        """Return candidate matches and evidence rows."""

        holdings = holdings_df.fillna("")
        sanctions = sanctions_df.fillna("")
        match_rows: list[dict[str, Any]] = []
        evidence_rows: list[dict[str, Any]] = []

        sanctions_records = []
        for sanction in sanctions.to_dict(orient="records"):
            identifiers = {
                field: normalize_identifier(sanction.get(field))
                for field in IDENTIFIER_FIELDS
                if sanction.get(field)
            }
            aliases = expand_aliases(
                sanction.get("primary_name"), self._coerce_aliases(sanction.get("aliases_json"))
            )
            sanctions_records.append(
                {
                    **sanction,
                    "identifiers": identifiers,
                    "name_candidates": aliases or [normalize_name(sanction.get("primary_name"))],
                    "primary_name_normalized": normalize_name(sanction.get("primary_name")),
                }
            )

        for holding in holdings.to_dict(orient="records"):
            holding_identifiers = {
                field: normalize_identifier(holding.get(field))
                for field in IDENTIFIER_FIELDS
                if holding.get(field)
            }
            holding_name = normalize_name(holding.get("issuer_name"))
            for sanction in sanctions_records:
                identifier_hits = [
                    field
                    for field, value in holding_identifiers.items()
                    if value and value == sanction["identifiers"].get(field)
                ]
                exact_name = holding_name and holding_name == sanction["primary_name_normalized"]
                alias_hit = holding_name in sanction["name_candidates"]

                token_sort = max(
                    fuzz.token_sort_ratio(holding_name, candidate)
                    for candidate in sanction["name_candidates"]
                )
                token_set = max(
                    fuzz.token_set_ratio(holding_name, candidate)
                    for candidate in sanction["name_candidates"]
                )
                partial = max(
                    fuzz.partial_ratio(holding_name, candidate)
                    for candidate in sanction["name_candidates"]
                )
                fuzzy_score = round((0.4 * token_set) + (0.35 * token_sort) + (0.25 * partial), 2)
                raw_score = fuzzy_score
                match_type = "fuzzy_name"

                if identifier_hits:
                    raw_score = 100.0
                    match_type = "identifier_match"
                elif exact_name:
                    raw_score = max(raw_score, 96.0)
                    match_type = "exact_normalized_name"
                elif alias_hit:
                    raw_score = max(raw_score, 94.0)
                    match_type = "alias_match"

                if (
                    holding.get("country")
                    and sanction.get("country")
                    and holding["country"] == sanction["country"]
                ):
                    raw_score = min(100.0, raw_score + 3.0)
                if sanction.get("entity_type", "").upper() == "INDIVIDUAL":
                    raw_score = max(0.0, raw_score - 12.0)

                confidence = self._confidence_band(
                    raw_score, identifier_hits, exact_name or alias_hit
                )
                if confidence is None:
                    continue

                explanation = self._explanation(
                    holding_name=holding_name,
                    sanction_name=sanction["primary_name_normalized"],
                    match_type=match_type,
                    score=raw_score,
                    identifier_hits=identifier_hits,
                    country_overlap=holding.get("country") == sanction.get("country"),
                )
                match_rows.append(
                    {
                        "run_id": run_id,
                        "fund_id": holding["fund_id"],
                        "holding_id": holding["holding_id"],
                        "sanctions_entity_id": sanction["sanctions_entity_id"],
                        "source_system": sanction["source_system"],
                        "match_type": match_type,
                        "raw_score": float(round(raw_score, 2)),
                        "confidence_band": confidence,
                        "explanation": explanation,
                        "review_status": "Pending",
                    }
                )
                evidence_rows.extend(
                    [
                        {
                            "run_id": run_id,
                            "fund_id": holding["fund_id"],
                            "holding_id": holding["holding_id"],
                            "sanctions_entity_id": sanction["sanctions_entity_id"],
                            "evidence_type": "score",
                            "evidence_key": "token_sort_ratio",
                            "evidence_value": str(round(token_sort, 2)),
                        },
                        {
                            "run_id": run_id,
                            "fund_id": holding["fund_id"],
                            "holding_id": holding["holding_id"],
                            "sanctions_entity_id": sanction["sanctions_entity_id"],
                            "evidence_type": "score",
                            "evidence_key": "token_set_ratio",
                            "evidence_value": str(round(token_set, 2)),
                        },
                        {
                            "run_id": run_id,
                            "fund_id": holding["fund_id"],
                            "holding_id": holding["holding_id"],
                            "sanctions_entity_id": sanction["sanctions_entity_id"],
                            "evidence_type": "score",
                            "evidence_key": "partial_ratio",
                            "evidence_value": str(round(partial, 2)),
                        },
                        {
                            "run_id": run_id,
                            "fund_id": holding["fund_id"],
                            "holding_id": holding["holding_id"],
                            "sanctions_entity_id": sanction["sanctions_entity_id"],
                            "evidence_type": "match",
                            "evidence_key": "identifier_hits",
                            "evidence_value": ",".join(identifier_hits)
                            if identifier_hits
                            else "none",
                        },
                    ]
                )

        matches_df = pd.DataFrame(match_rows)
        if not matches_df.empty:
            matches_df = matches_df.sort_values(
                ["raw_score", "confidence_band"], ascending=[False, True]
            )
        return MatchResultBundle(matches=matches_df, evidence=pd.DataFrame(evidence_rows))

    @staticmethod
    def _coerce_aliases(value: Any) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except json.JSONDecodeError:
                return [value]
        return [str(value)]

    def _confidence_band(
        self, raw_score: float, identifier_hits: list[str], strong_name_support: bool
    ) -> str | None:
        if identifier_hits or (
            strong_name_support and raw_score >= self.settings.match_high_threshold
        ):
            return "High"
        if raw_score >= self.settings.match_medium_threshold:
            return "Medium"
        if raw_score >= self.settings.match_low_threshold:
            return "Low"
        return None

    @staticmethod
    def _explanation(
        holding_name: str,
        sanction_name: str,
        match_type: str,
        score: float,
        identifier_hits: list[str],
        country_overlap: bool,
    ) -> str:
        parts = [
            f"Holding '{holding_name}' compared with sanctions entity '{sanction_name}'.",
            f"Match type: {match_type}.",
            f"Composite score: {round(score, 2)}.",
        ]
        if identifier_hits:
            parts.append(f"Identifier overlap on {', '.join(identifier_hits)}.")
        if country_overlap:
            parts.append("Country overlap boosted confidence.")
        return " ".join(parts)
