with ranked as (
    select
        md5(source_system || ':' || source_record_id) as sanctions_entity_id,
        source_system,
        source_record_id,
        raw_payload->>'primary_name' as primary_name,
        coalesce(raw_payload->'alternate_names', raw_payload->'aliases_json', '[]'::jsonb) as aliases_json,
        coalesce(raw_payload->>'entity_type', 'Entity') as entity_type,
        raw_payload->>'program' as program,
        raw_payload->>'country' as country,
        raw_payload->>'nationality' as nationality,
        raw_payload->>'date_of_birth' as date_of_birth,
        raw_payload->>'place_of_birth' as place_of_birth,
        raw_payload->>'remarks' as remarks,
        nullif(raw_payload->>'isin', '') as isin,
        nullif(raw_payload->>'cusip', '') as cusip,
        nullif(raw_payload->>'sedol', '') as sedol,
        nullif(raw_payload->>'ticker', '') as ticker,
        source_last_updated,
        coalesce(raw_payload->>'source_url', source_url) as source_url,
        raw_payload,
        ingested_at,
        row_number() over (
            partition by source_system, source_record_id
            order by ingested_at desc
        ) as row_num
    from {{ source('app_raw', 'raw_sanctions_record') }}
)
select
    sanctions_entity_id,
    source_system,
    source_record_id,
    primary_name,
    aliases_json,
    entity_type,
    program,
    country,
    nationality,
    date_of_birth,
    place_of_birth,
    remarks,
    isin,
    cusip,
    sedol,
    ticker,
    source_last_updated,
    source_url,
    raw_payload,
    ingested_at
from ranked
where row_num = 1

