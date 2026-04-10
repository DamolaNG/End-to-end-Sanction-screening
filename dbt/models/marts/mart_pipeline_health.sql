with latest_snapshots as (
    select
        source_system,
        dataset_name,
        extraction_mode,
        ingestion_ts,
        source_last_updated,
        row_count,
        row_number() over (partition by source_system, dataset_name order by ingestion_ts desc) as row_num
    from raw_source_snapshot
),
latest_dq as (
    select
        source_system,
        check_name,
        severity,
        status,
        issue_message,
        affected_count,
        created_at,
        row_number() over (partition by source_system, check_name order by created_at desc) as row_num
    from data_quality_issue
)
select
    s.source_system,
    s.dataset_name,
    s.extraction_mode,
    s.ingestion_ts,
    s.source_last_updated,
    s.row_count,
    d.check_name,
    d.severity,
    d.status,
    d.issue_message,
    d.affected_count,
    d.created_at as last_quality_event_at
from latest_snapshots s
left join latest_dq d
    on s.source_system = d.source_system
    and d.row_num = 1
where s.row_num = 1

