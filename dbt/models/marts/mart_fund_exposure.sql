select
    m.run_id,
    f.fund_id,
    f.fund_name,
    f.asset_class,
    f.domicile,
    count(distinct m.match_id) as candidate_match_count,
    count(distinct case when m.confidence_band = 'High' then m.match_id end) as high_match_count,
    count(distinct h.issuer_name) as unique_flagged_issuers
from screening_match m
join {{ ref('int_curated_funds') }} f
    on m.fund_id = f.fund_id
join {{ ref('int_curated_holdings') }} h
    on m.holding_id = h.holding_id
group by 1, 2, 3, 4, 5

