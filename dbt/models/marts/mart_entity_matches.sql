select
    m.match_id,
    m.run_id,
    m.source_system,
    m.confidence_band,
    m.match_type,
    m.raw_score,
    m.explanation,
    m.review_status,
    f.fund_id,
    f.fund_name,
    h.holding_id,
    h.issuer_name,
    h.country as holding_country,
    s.sanctions_entity_id,
    s.primary_name as sanctions_name,
    s.entity_type,
    s.program,
    s.country as sanctions_country,
    s.aliases_json,
    s.source_url
from screening_match m
join {{ ref('int_curated_funds') }} f
    on m.fund_id = f.fund_id
join {{ ref('int_curated_holdings') }} h
    on m.holding_id = h.holding_id
join {{ ref('int_curated_sanctions_entities') }} s
    on m.sanctions_entity_id = s.sanctions_entity_id

