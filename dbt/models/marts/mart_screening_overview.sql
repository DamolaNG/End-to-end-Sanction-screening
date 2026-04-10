select
    run_id,
    started_at,
    finished_at,
    status,
    mode,
    total_funds_screened,
    total_holdings_screened,
    total_sanctions_entities,
    candidate_matches_count,
    high_match_count,
    medium_match_count,
    low_match_count,
    stale_source_warning_count,
    case
        when total_funds_screened = 0 then 0
        else round(candidate_matches_count::numeric / total_funds_screened, 2)
    end as average_candidate_matches_per_fund
from screening_run

