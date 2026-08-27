# ADR 0003: SQLite for evaluation and PostgreSQL for production

- Status: Accepted
- Date: 2026-08-27

## Context

A portfolio reviewer should run the project without infrastructure, while the production
architecture should support dbt, concurrency, backups, and managed deployment.

## Decision

Keep domain/repository behavior portable through SQLAlchemy. Use SQLite for tests and zero-
service evaluation; use PostgreSQL for container and production deployments.

## Consequences

- Core behavior is easy to review and test.
- dbt models target PostgreSQL and are not part of the SQLite quick start.
- Database-specific optimization must remain behind the repository boundary.
