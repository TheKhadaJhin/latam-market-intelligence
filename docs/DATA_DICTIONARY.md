# Data Dictionary

## Application tables

### `countries`

| Column | Type | Meaning |
| --- | --- | --- |
| `code` | string(3) | ISO3 country key |
| `name` | string | Display name |
| `region` | string | Comparison region label |

### `indicators`

| Column | Type | Meaning |
| --- | --- | --- |
| `code` | string | World Bank indicator code |
| `name` | string | Business-readable name |
| `unit` | string | Source measurement unit |
| `category` | string | Score dimension |
| `polarity` | enum | Whether high or low values are favorable |
| `base_weight` | float | Balanced scenario weight |

### `observations`

Primary key: `(country_code, indicator_code, year)`.

| Column | Type | Meaning |
| --- | --- | --- |
| `country_code` | string(3) | Country key |
| `indicator_code` | string | Indicator key |
| `year` | integer | Source observation year |
| `value` | float | Non-null numeric source value |
| `source_updated_at` | string/date | World Bank dataset update metadata |
| `fetched_at` | timestamp | UTC ingestion timestamp |

### `market_scores`

Unique key: `(country_code, reference_year, scenario)`.

| Column | Type | Meaning |
| --- | --- | --- |
| `overall_score` | float | Coverage-adjusted `0–100` score |
| `coverage_ratio` | float | Available weighted coverage |
| `rank` | integer | Relative rank inside the scenario/year |
| `dimensions_json` | JSON text | Category-level scores |
| `indicator_scores_json` | JSON text | Normalized indicator contributions |
| `indicator_years_json` | JSON text | Actual source year selected per indicator |
| `calculated_at` | timestamp | UTC materialization time |

### `pipeline_runs`

| Column | Type | Meaning |
| --- | --- | --- |
| `run_id` | UUID string | Pipeline audit identifier |
| `status` | enum | `running`, `succeeded`, or `failed` |
| `records_received` | integer | Valid non-null source observations |
| `records_upserted` | integer | Idempotently processed records |
| `rankings_calculated` | integer | Materialized country/scenario rows |
| `reference_year` | integer | Scoring year selected by the run |
| `started_at`, `completed_at` | timestamp | UTC run boundaries |
| `source_updated_at` | string/date | Newest upstream update metadata |
| `error` | text | Sanitized failure class and message |

## dbt marts

- `fct_market_observations`: observation fact enriched with country and indicator attributes.
- `mart_latest_indicator_values`: latest known observation by country and indicator.
- `mart_data_coverage`: completeness and recency controls by country.
