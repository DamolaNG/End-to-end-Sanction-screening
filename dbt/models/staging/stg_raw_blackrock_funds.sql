with ranked as (
    select
        raw_payload->>'fund_id' as fund_id,
        raw_payload->>'fund_name' as fund_name,
        raw_payload->>'share_class' as share_class,
        raw_payload->>'isin' as isin,
        raw_payload->>'sedol' as sedol,
        raw_payload->>'fund_type' as fund_type,
        raw_payload->>'domicile' as domicile,
        raw_payload->>'asset_class' as asset_class,
        raw_payload->>'currency' as currency,
        raw_payload->>'blackrock_url' as blackrock_url,
        (raw_payload->>'snapshot_date')::date as snapshot_date,
        raw_payload,
        ingested_at,
        row_number() over (partition by raw_payload->>'fund_id' order by ingested_at desc) as row_num
    from {{ source('app_raw', 'raw_blackrock_fund_record') }}
)
select
    fund_id,
    fund_name,
    share_class,
    isin,
    sedol,
    fund_type,
    domicile,
    asset_class,
    currency,
    blackrock_url,
    snapshot_date,
    raw_payload,
    ingested_at
from ranked
where row_num = 1

