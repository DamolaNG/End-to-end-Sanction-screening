"""Pandera-based data contracts."""

from __future__ import annotations

import pandera as pa
from pandera import Check


sanctions_contract = pa.DataFrameSchema(
    {
        "source_record_id": pa.Column(str, nullable=False),
        "primary_name": pa.Column(str, nullable=False),
        "entity_type": pa.Column(str, nullable=False),
    },
    strict=False,
    coerce=True,
)

fund_contract = pa.DataFrameSchema(
    {
        "fund_id": pa.Column(str, nullable=False),
        "fund_name": pa.Column(str, nullable=False),
        "isin": pa.Column(str, nullable=True),
    },
    strict=False,
    coerce=True,
)

holding_contract = pa.DataFrameSchema(
    {
        "holding_id": pa.Column(str, nullable=False),
        "fund_id": pa.Column(str, nullable=False),
        "issuer_name": pa.Column(str, nullable=False),
        "snapshot_date": pa.Column(object, nullable=False),
    },
    strict=False,
    coerce=True,
)

match_contract = pa.DataFrameSchema(
    {
        "fund_id": pa.Column(str, nullable=False),
        "holding_id": pa.Column(str, nullable=False),
        "sanctions_entity_id": pa.Column(str, nullable=False),
        "source_system": pa.Column(str, nullable=False),
        "match_type": pa.Column(str, nullable=False),
        "raw_score": pa.Column(float, nullable=False, checks=Check.in_range(0, 100)),
        "confidence_band": pa.Column(str, nullable=False),
    },
    strict=False,
    coerce=True,
)
