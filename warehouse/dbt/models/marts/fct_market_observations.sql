select
    o.country_code,
    c.country_name,
    c.region,
    o.indicator_code,
    i.indicator_name,
    i.unit,
    i.category,
    i.polarity,
    i.base_weight,
    o.year,
    o.value,
    o.source_updated_at,
    o.fetched_at
from {{ ref('stg_observations') }} as o
inner join {{ ref('stg_countries') }} as c using (country_code)
inner join {{ ref('stg_indicators') }} as i using (indicator_code)
