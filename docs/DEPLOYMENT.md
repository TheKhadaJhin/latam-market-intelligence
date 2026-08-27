# Deployment Guide

## Local PostgreSQL deployment

1. Copy `.env.example` to `.env` and replace development credentials.
2. Run `docker compose up -d db api`.
3. Run `docker compose --profile pipeline run --rm pipeline`.
4. Run `docker compose up -d dashboard`.
5. Verify `/health`, `/ready`, and the dashboard.

## Production requirements

- Use managed PostgreSQL with TLS, backups, point-in-time recovery, and least-privilege users.
- Store secrets in the platform secret manager; never bake `.env` into an image.
- Run Alembic as a release job before starting new application replicas.
- Schedule the Prefect flow or one-shot pipeline container; do not run independent schedulers
  inside every API replica.
- Persist raw lineage in durable object storage or a restricted volume.
- Put the API behind TLS, authentication/rate limiting if exposed, and a reverse proxy.
- Restrict `/metrics` and the database to private networks.
- Send structured logs and Prometheus metrics to centralized observability systems.
- Pin deployed images by digest and scan them before release.

## Environment variables

All variables use the `MARKET_INTEL_` prefix. See `.env.example` for the complete set.
Production requires `ENVIRONMENT=production` and a PostgreSQL `DATABASE_URL`.

## Safe rollout

1. Back up the database.
2. Apply migrations in a release job.
3. Deploy the API and verify liveness/readiness.
4. Run the pipeline once and inspect the audit row, coverage, and source metadata.
5. Deploy the dashboard.
6. Roll back the application image if health checks fail; do not automatically downgrade
   database migrations without reviewing data-loss risk.
