import asyncio
import csv
import io
from pathlib import Path

import pytest
from sqlalchemy import Engine

from market_intel.config import Settings
from market_intel.domain import Scenario
from market_intel.repository import MarketRepository
from market_intel.services.pipeline import run_pipeline
from market_intel.services.world_bank import SnapshotSource


@pytest.mark.asyncio
async def test_committed_snapshot_reproduces_expected_base_ranking(
    database: tuple[Engine, MarketRepository],
) -> None:
    _, repository = database
    source = SnapshotSource(Path("data/sample/world_bank_snapshot.json"))
    settings = Settings(database_url="sqlite://")

    result = await run_pipeline(
        source=source,
        repository=repository,
        settings=settings,
        start_year=2015,
        end_year=2026,
        persist_raw=False,
    )
    actual = repository.get_scores(scenario=Scenario.BASE)
    expected_text = await asyncio.to_thread(
        Path("data/sample/expected_rankings_base.csv").read_text, encoding="utf-8"
    )
    expected = list(csv.DictReader(io.StringIO(expected_text)))

    assert result.records_received == 518
    assert result.reference_year == 2025
    assert [item.country_code for item in actual] == [row["country_code"] for row in expected]
    assert [item.overall_score for item in actual] == [
        float(row["overall_score"]) for row in expected
    ]
