with ranked as (
    select
        raw_payload->>'holding_id' as holding_id,
        raw_payload->>'fund_id' as fund_id,
        raw_payload->>'issuer_name' as issuer_name,
        raw_payload->>'isin' as isin,
        raw_payload->>'ticker' as ticker,
        raw_payload->>'cusip' as cusip,
        raw_payload->>'sedol' as sedol,
        raw_payload->>'country' as country,
        raw_payload->>'sector' as sector,
        nullif(raw_payload->>'market_value', '')::numeric as market_value,
        nullif(raw_payload->>'weight_pct', '')::numeric as weight_pct,
        (raw_payload->>'snapshot_date')::date as snapshot_date,
        raw_payload->>'source_url' as source_url,
        raw_payload,
        ingested_at,
        row_number() over (partition by raw_payload->>'holding_id' order by ingested_at desc) as row_num
    from {{ source('app_raw', 'raw_blackrock_holding_record') }}
)
select
    holding_id,
    fund_id,
    issuer_name,
    isin,
    ticker,
    cusip,
    sedol,
    country,
    sector,
    market_value,
    weight_pct,
    snapshot_date,
    source_url,
    raw_payload,
    ingested_at
from ranked
where row_num = 1

