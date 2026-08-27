import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import structlog

from market_intel.catalog import INDICATORS
from market_intel.config import Settings
from market_intel.domain import IndicatorDefinition, PipelineResult, RunStatus, Scenario
from market_intel.repository import MarketRepository
from market_intel.services.scoring import calculate_scores
from market_intel.services.world_bank import FetchResult, IndicatorSource

logger = structlog.get_logger()


async def run_pipeline(
    *,
    source: IndicatorSource,
    repository: MarketRepository,
    settings: Settings,
    start_year: int,
    end_year: int,
    persist_raw: bool = True,
) -> PipelineResult:
    run_id = str(uuid4())
    result = PipelineResult(
        run_id=run_id,
        status=RunStatus.RUNNING,
        started_at=datetime.now(UTC),
    )
    repository.create_run(result)
    repository.seed_catalog()
    logger.info("pipeline_started", run_id=run_id, start_year=start_year, end_year=end_year)

    try:
        semaphore = asyncio.Semaphore(4)

        async def fetch_one(indicator: IndicatorDefinition) -> FetchResult:
            async with semaphore:
                return await source.fetch_indicator(indicator, start_year, end_year)

        fetch_results = await asyncio.gather(*(fetch_one(item) for item in INDICATORS))
        records = [record for item in fetch_results for record in item.records]
        source_updates = [
            item.source_updated_at for item in fetch_results if item.source_updated_at
        ]

        if persist_raw:
            _persist_raw_payloads(settings.raw_data_dir, run_id, fetch_results)

        records_upserted = repository.upsert_observations(records)
        reference_year = max((record.year for record in records), default=end_year)
        all_observations = repository.list_observations(end_year=reference_year)
        rankings_calculated = 0
        for scenario in Scenario:
            scores = calculate_scores(
                all_observations,
                reference_year=reference_year,
                scenario=scenario,
                max_staleness_years=settings.max_staleness_years,
                minimum_coverage_ratio=settings.minimum_coverage_ratio,
            )
            rankings_calculated += repository.replace_scores(reference_year, scenario, scores)

        result = result.model_copy(
            update={
                "status": RunStatus.SUCCEEDED,
                "records_received": len(records),
                "records_upserted": records_upserted,
                "rankings_calculated": rankings_calculated,
                "reference_year": reference_year,
                "completed_at": datetime.now(UTC),
                "source_updated_at": max(source_updates) if source_updates else None,
            }
        )
        repository.finish_run(result)
        logger.info(
            "pipeline_succeeded",
            run_id=run_id,
            records=len(records),
            rankings=rankings_calculated,
        )
        return result
    except Exception as exc:
        failed = result.model_copy(
            update={
                "status": RunStatus.FAILED,
                "completed_at": datetime.now(UTC),
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        repository.finish_run(failed)
        logger.exception("pipeline_failed", run_id=run_id)
        raise


def _persist_raw_payloads(raw_data_dir: Path, run_id: str, results: list[FetchResult]) -> None:
    run_directory = raw_data_dir / run_id
    run_directory.mkdir(parents=True, exist_ok=True)
    for indicator, result in zip(INDICATORS, results, strict=True):
        destination = run_directory / f"{indicator.code}.json"
        destination.write_text(
            json.dumps(result.raw_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
