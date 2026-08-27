select sum(base_weight) as total_weight
from {{ ref('stg_indicators') }}
having abs(sum(base_weight) - 1.0) > 0.000001
