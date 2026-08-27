select
    upper(country_code) as country_code,
    indicator_code,
    year,
    value,
    nullif(source_updated_at, '') as source_updated_at,
    fetched_at
from {{ source('application', 'observations') }}
where year between 1960 and 2100
