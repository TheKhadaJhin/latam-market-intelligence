.PHONY: install format lint typecheck test security check sample pipeline api dashboard dbt

install:
	uv sync --group dev

format:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff format --check .
	uv run ruff check .

typecheck:
	uv run mypy src

test:
	uv run pytest --cov=market_intel --cov-report=term-missing --cov-report=xml

security:
	uv run bandit -c pyproject.toml -r src
	uv run pip-audit

check: lint typecheck test security

sample:
	uv run python scripts/download_snapshot.py

pipeline:
	uv run market-intel pipeline --snapshot data/sample/world_bank_snapshot.json

api:
	uv run uvicorn market_intel.main:app --reload

dashboard:
	uv run --extra dashboard streamlit run dashboard/app.py

dbt:
	cd warehouse/dbt && uv run --extra warehouse dbt build --profiles-dir .
