select
    code as indicator_code,
    trim(name) as indicator_name,
    trim(unit) as unit,
    trim(category) as category,
    polarity,
    base_weight
from {{ source('application', 'indicators') }}
