# Operational Runbook

## Pipeline failure

1. Check the latest `/v1/pipeline-runs` entry or structured logs using its `run_id`.
2. Distinguish timeout/HTTP failure from source-contract drift or database failure.
3. Verify the World Bank endpoint manually for one configured indicator.
4. Retry once after the upstream issue clears; replay is idempotent.
5. Use the committed snapshot if a demonstration must continue offline.
6. Do not mark a failed run successful or overwrite the last valid score partition manually.

## Readiness returns 503

- `database=false`: validate URL, credentials, TLS, network policy, and migration status.
- `database=true`, `observations=0`: run the pipeline or load the snapshot.
- Database available but API errors: compare current schema with the Alembic head.

## Coverage below threshold

1. Inspect `mart_data_coverage` and the indicator years returned in each ranking.
2. Confirm whether the source has delayed or discontinued the series.
3. Do not replace a missing value with zero or a peer average without an approved methodology
   revision.
4. If a source change is permanent, document the replacement indicator and add an ADR.

## Unexpected ranking change

1. Compare source update metadata and raw payloads by run ID.
2. Compare actual indicator years, scenario weights, and coverage.
3. Run all tests and reproduce from the previous snapshot.
4. Explain whether the change comes from source revision, new year, missingness, or code.

## Recovery

- Restore PostgreSQL from the last verified backup if data is corrupted.
- Re-run a known snapshot to reconstruct normalized observations and scores.
- Raw source payloads and pipeline audit rows provide lineage; they are not a database backup.
