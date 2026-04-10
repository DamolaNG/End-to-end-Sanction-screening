select
    holding_id,
    fund_id,
    issuer_name,
    regexp_replace(
        trim(regexp_replace(upper(coalesce(issuer_name, '')), '[^A-Z0-9 ]', ' ', 'g')),
        '\s+',
        ' ',
        'g'
    ) as issuer_name_normalized,
    isin,
    ticker,
    cusip,
    sedol,
    country,
    sector,
    market_value,
    weight_pct,
    snapshot_date,
    source_url
from {{ ref('stg_raw_blackrock_holdings') }}

