with expected as (
    select count(*)::numeric as expected_indicators
    from {{ ref('stg_indicators') }}
),
observed as (
    select
        country_code,
        country_name,
        count(distinct indicator_code)::numeric as observed_indicators,
        min(year) as oldest_latest_year,
        max(year) as newest_latest_year
    from {{ ref('mart_latest_indicator_values') }}
    group by 1, 2
)

select
    observed.country_code,
    observed.country_name,
    observed.observed_indicators,
    expected.expected_indicators,
    round(observed.observed_indicators / nullif(expected.expected_indicators, 0), 4) as coverage_ratio,
    observed.oldest_latest_year,
    observed.newest_latest_year
from observed
cross join expected
