import asyncio
import csv
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
from sqlalchemy import Engine

from market_intel.catalog import INDICATORS
from market_intel.config import Settings
from market_intel.database import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from market_intel.domain import Scenario
from market_intel.logging import configure_logging
from market_intel.repository import MarketRepository
from market_intel.services.pipeline import run_pipeline
from market_intel.services.world_bank import SnapshotSource, WorldBankClient

app = typer.Typer(help="Build and operate the LATAM Market Intelligence data product.")


def _repository(settings: Settings) -> tuple[Engine, MarketRepository]:
    engine = create_database_engine(settings.database_url)
    initialize_database(engine)
    session = create_session_factory(engine)()
    return engine, MarketRepository(session)


@app.command("init-db")
def init_db() -> None:
    """Create database tables and seed the country/indicator catalog."""
    settings = Settings()
    engine, repository = _repository(settings)
    try:
        repository.seed_catalog()
        typer.echo("Database initialized and catalog seeded.")
    finally:
        repository.session.close()
        engine.dispose()


@app.command("pipeline")
def pipeline_command(
    start_year: Annotated[int, typer.Option(min=1960, max=2100)] = 2015,
    end_year: Annotated[int, typer.Option(min=1960, max=2100)] = datetime.now(UTC).year,
    snapshot: Annotated[
        Path | None,
        typer.Option(help="Use an offline World Bank snapshot instead of the live API."),
    ] = None,
    persist_raw: Annotated[bool, typer.Option()] = True,
) -> None:
    """Run extraction, loading, scoring, and ranking materialization."""
    if start_year > end_year:
        raise typer.BadParameter("start-year must be less than or equal to end-year")
    settings = Settings()
    configure_logging(settings.log_level, json_logs=settings.is_production)
    engine, repository = _repository(settings)

    async def execute() -> None:
        if snapshot:
            source = SnapshotSource(snapshot)
            result = await run_pipeline(
                source=source,
                repository=repository,
                settings=settings,
                start_year=start_year,
                end_year=end_year,
                persist_raw=False,
            )
        else:
            async with WorldBankClient(
                base_url=settings.world_bank_base_url,
                timeout_seconds=settings.request_timeout_seconds,
                retries=settings.request_retries,
            ) as live_source:
                result = await run_pipeline(
                    source=live_source,
                    repository=repository,
                    settings=settings,
                    start_year=start_year,
                    end_year=end_year,
                    persist_raw=persist_raw,
                )
        typer.echo(result.model_dump_json(indent=2))

    try:
        asyncio.run(execute())
    finally:
        repository.session.close()
        engine.dispose()


@app.command("export-rankings")
def export_rankings(
    destination: Path = Path("data/exports/rankings.csv"),
    scenario: Scenario = Scenario.BASE,
    year: int | None = None,
) -> None:
    """Export materialized rankings as a business-friendly CSV file."""
    settings = Settings()
    engine, repository = _repository(settings)
    try:
        rankings = repository.get_scores(reference_year=year, scenario=scenario)
        if not rankings:
            raise typer.BadParameter("no rankings are available; run the pipeline first")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "rank",
                    "country_code",
                    "country_name",
                    "reference_year",
                    "scenario",
                    "overall_score",
                    "coverage_ratio",
                ],
            )
            writer.writeheader()
            for item in rankings:
                writer.writerow(
                    {
                        "rank": item.rank,
                        "country_code": item.country_code,
                        "country_name": item.country_name,
                        "reference_year": item.reference_year,
                        "scenario": item.scenario.value,
                        "overall_score": item.overall_score,
                        "coverage_ratio": item.coverage_ratio,
                    }
                )
        typer.echo(f"Exported {len(rankings)} rows to {destination}")
    finally:
        repository.session.close()
        engine.dispose()


@app.command("catalog")
def show_catalog() -> None:
    """Display the configured indicators and transparent base weights."""
    for indicator in INDICATORS:
        typer.echo(
            f"{indicator.code}\t{indicator.name}\t{indicator.polarity.value}\t"
            f"{indicator.base_weight:.2f}"
        )
