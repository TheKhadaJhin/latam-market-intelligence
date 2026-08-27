select
    upper(code) as country_code,
    trim(name) as country_name,
    trim(region) as region
from {{ source('application', 'countries') }}
