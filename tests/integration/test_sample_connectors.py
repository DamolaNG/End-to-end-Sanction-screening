from app.connectors.blackrock import BlackRockFundConnector, BlackRockHoldingsConnector
from app.connectors.sanctions import (
    EUSanctionsConnector,
    OFACSanctionsConnector,
    UNSanctionsConnector,
)


def test_sample_connectors_load_records() -> None:
    connectors = [
        UNSanctionsConnector(),
        EUSanctionsConnector(),
        OFACSanctionsConnector(),
        BlackRockFundConnector(),
        BlackRockHoldingsConnector(),
    ]
    for connector in connectors:
        result = connector.run()
        assert result.row_count > 0
        assert result.file_hash
