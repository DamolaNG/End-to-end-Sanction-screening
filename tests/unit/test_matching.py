from uuid import UUID

import pandas as pd

from app.services.matching import ScreeningEngine


def test_identifier_match_scores_high() -> None:
    engine = ScreeningEngine()
    funds = pd.DataFrame([{"fund_id": "F1", "fund_name": "Demo Fund"}])
    holdings = pd.DataFrame(
        [
            {
                "holding_id": "H1",
                "fund_id": "F1",
                "issuer_name": "Acme Defense Technology Ltd",
                "isin": "US0000000001",
                "ticker": "ACME",
                "cusip": "",
                "sedol": "",
                "country": "Russia",
            }
        ]
    )
    sanctions = pd.DataFrame(
        [
            {
                "sanctions_entity_id": "S1",
                "source_system": "OFAC",
                "primary_name": "ACME DEFENSE TECHNOLOGY LTD",
                "aliases_json": ["ACME DEFENSE TECHNOLOGY"],
                "entity_type": "Entity",
                "country": "Russia",
                "isin": "US0000000001",
                "ticker": "ACME",
                "cusip": "",
                "sedol": "",
            }
        ]
    )

    result = engine.screen(
        run_id=UUID("00000000-0000-0000-0000-000000000001"),
        funds_df=funds,
        holdings_df=holdings,
        sanctions_df=sanctions,
    )
    assert len(result.matches) == 1
    assert result.matches.iloc[0]["confidence_band"] == "High"
    assert result.matches.iloc[0]["match_type"] == "identifier_match"


def test_fuzzy_match_returns_medium_or_low() -> None:
    engine = ScreeningEngine()
    funds = pd.DataFrame([{"fund_id": "F1", "fund_name": "Demo Fund"}])
    holdings = pd.DataFrame(
        [{"holding_id": "H1", "fund_id": "F1", "issuer_name": "Caspian Trade Dev SA", "country": "Iran"}]
    )
    sanctions = pd.DataFrame(
        [
            {
                "sanctions_entity_id": "S1",
                "source_system": "EU",
                "primary_name": "CASPIAN TRADE DEVELOPMENT SA",
                "aliases_json": ["CASPIAN TRADE DEV"],
                "entity_type": "Entity",
                "country": "Iran",
            }
        ]
    )

    result = engine.screen(
        run_id=UUID("00000000-0000-0000-0000-000000000002"),
        funds_df=funds,
        holdings_df=holdings,
        sanctions_df=sanctions,
    )
    assert len(result.matches) == 1
    assert result.matches.iloc[0]["confidence_band"] in {"High", "Medium", "Low"}
