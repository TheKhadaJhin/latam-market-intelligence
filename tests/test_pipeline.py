from pathlib import Path

import pytest
from sqlalchemy import Engine

from market_intel.config import Settings
from market_intel.domain import RunStatus, Scenario
from market_intel.repository import MarketRepository
from market_intel.services.pipeline import run_pipeline
from tests.helpers import FakeSource


@pytest.mark.asyncio
async def test_pipeline_persists_raw_data_observations_and_all_scenarios(
    database: tuple[Engine, MarketRepository], tmp_path: Path
) -> None:
    _, repository = database
    settings = Settings(
        database_url="sqlite://",
        raw_data_dir=tmp_path / "raw",
        minimum_coverage_ratio=0.75,
    )

    result = await run_pipeline(
        source=FakeSource(),
        repository=repository,
        settings=settings,
        start_year=2020,
        end_year=2024,
    )

    assert result.status == RunStatus.SUCCEEDED
    assert result.records_received == 48
    assert result.records_upserted == 48
    assert result.rankings_calculated == 18
    assert result.reference_year == 2024
    assert len(list((tmp_path / "raw" / result.run_id).glob("*.json"))) == 8
    assert len(repository.get_scores(scenario=Scenario.GROWTH)) == 6
    assert repository.list_runs()[0].status == RunStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_pipeline_records_failure_and_preserves_exception(
    database: tuple[Engine, MarketRepository], tmp_path: Path
) -> None:
    _, repository = database
    settings = Settings(database_url="sqlite://", raw_data_dir=tmp_path / "raw")

    with pytest.raises(RuntimeError, match="upstream unavailable"):
        await run_pipeline(
            source=FakeSource(fail=True),
            repository=repository,
            settings=settings,
            start_year=2020,
            end_year=2024,
        )

    failed = repository.list_runs()[0]
    assert failed.status == RunStatus.FAILED
    assert "upstream unavailable" in (failed.error or "")
