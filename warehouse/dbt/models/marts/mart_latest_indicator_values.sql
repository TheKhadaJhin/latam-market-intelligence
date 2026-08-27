with ranked as (
    select
        *,
        row_number() over (
            partition by country_code, indicator_code
            order by year desc, fetched_at desc
        ) as recency_rank
    from {{ ref('fct_market_observations') }}
)

select
    country_code,
    country_name,
    indicator_code,
    indicator_name,
    unit,
    category,
    polarity,
    year,
    value,
    source_updated_at
from ranked
where recency_rank = 1
