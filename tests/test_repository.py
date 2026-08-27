from datetime import UTC, datetime

from sqlalchemy import Engine

from market_intel.domain import PipelineResult, RunStatus, Scenario
from market_intel.repository import MarketRepository
from market_intel.services.scoring import calculate_scores
from tests.helpers import observation_records


def test_repository_upsert_is_idempotent_and_filters_history(
    database: tuple[Engine, MarketRepository],
) -> None:
    _, repository = database
    records = observation_records()

    assert repository.upsert_observations(records) == len(records)
    assert repository.upsert_observations(records) == len(records)
    assert repository.count_observations() == len(records)
    assert repository.latest_observation_year() == 2024

    history = repository.list_observations(
        country_code="arg",
        indicator_code=records[0].indicator_code,
        start_year=2024,
        end_year=2024,
    )
    assert len(history) == 1
    assert history[0].country_name == "Argentina"


def test_repository_replaces_and_reads_scores(
    database: tuple[Engine, MarketRepository],
) -> None:
    _, repository = database
    records = observation_records()
    repository.upsert_observations(records)
    scores = calculate_scores(records, reference_year=2024)

    assert repository.replace_scores(2024, Scenario.BASE, scores) == 6
    first = repository.get_scores(scenario=Scenario.BASE)
    assert len(first) == 6
    assert first[0].rank == 1

    smaller = scores[:2]
    assert repository.replace_scores(2024, Scenario.BASE, smaller) == 2
    assert len(repository.get_scores(reference_year=2024)) == 2
    assert repository.get_scores(reference_year=1990) == []


def test_repository_tracks_pipeline_lifecycle(
    database: tuple[Engine, MarketRepository],
) -> None:
    _, repository = database
    started = datetime(2026, 8, 27, tzinfo=UTC)
    running = PipelineResult(run_id="run-1", status=RunStatus.RUNNING, started_at=started)
    repository.create_run(running)

    completed = running.model_copy(
        update={
            "status": RunStatus.SUCCEEDED,
            "completed_at": datetime(2026, 8, 27, 0, 1, tzinfo=UTC),
            "records_received": 48,
            "records_upserted": 48,
            "rankings_calculated": 18,
            "reference_year": 2024,
        }
    )
    repository.finish_run(completed)

    runs = repository.list_runs(limit=1)
    assert runs[0].status == RunStatus.SUCCEEDED
    assert runs[0].rankings_calculated == 18
    assert repository.latest_successful_run_at() is not None


def test_finish_run_creates_missing_audit_row(
    database: tuple[Engine, MarketRepository],
) -> None:
    _, repository = database
    result = PipelineResult(
        run_id="missing", status=RunStatus.FAILED, started_at=datetime.now(UTC), error="boom"
    )
    repository.finish_run(result)
    assert repository.list_runs()[0].error == "boom"
