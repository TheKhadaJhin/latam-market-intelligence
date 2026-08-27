# Contributing

Thank you for improving LATAM Market Intelligence.

## Development workflow

1. Create a focused branch from `main`.
2. Run `uv sync --group dev`.
3. Add or update tests with every behavior change.
4. Run `make check` before opening a pull request.
5. Explain business and methodology effects, not only implementation details.

## Pull requests

- Keep changes small and independently reviewable.
- Do not commit generated raw data, credentials, `.env`, local databases, or dbt targets.
- Document new indicators, sources, transformations, assumptions, and licenses.
- Add an ADR when changing source-of-truth, scoring, persistence, or orchestration decisions.
- Treat weight changes as methodology changes and include before/after evidence.

## Commit style

Use concise imperative messages such as:

- `feat: add market coverage endpoint`
- `fix: reject stale inflation values`
- `docs: explain resilience scenario`
