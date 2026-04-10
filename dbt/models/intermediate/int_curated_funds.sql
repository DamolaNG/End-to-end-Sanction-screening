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
    snapshot_date
from {{ ref('stg_raw_blackrock_funds') }}

