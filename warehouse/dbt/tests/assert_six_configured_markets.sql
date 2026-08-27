select count(*) as market_count
from {{ ref('stg_countries') }}
having count(*) != 6
