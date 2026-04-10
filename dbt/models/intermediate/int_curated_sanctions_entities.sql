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
    regexp_replace(
        trim(regexp_replace(upper(coalesce(primary_name, '')), '[^A-Z0-9 ]', ' ', 'g')),
        '\s+',
        ' ',
        'g'
    ) as primary_name_normalized,
    source_last_updated,
    source_url,
    raw_payload
from {{ ref('stg_raw_sanctions_entities') }}

