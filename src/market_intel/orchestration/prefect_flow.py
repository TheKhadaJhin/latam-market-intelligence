from datetime import UTC, datetime

from prefect import flow  # type: ignore[import-not-found]

from market_intel.config import Settings
from market_intel.database import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from market_intel.domain import PipelineResult
from market_intel.repository import MarketRepository
from market_intel.services.pipeline import run_pipeline
from market_intel.services.world_bank import WorldBankClient


@flow(name="latam-market-intelligence", log_prints=True)  # type: ignore[untyped-decorator]
async def market_intelligence_flow(
    start_year: int = 2015, end_year: int | None = None
) -> PipelineResult:
    """Scheduled Prefect entry point for the complete data pipeline."""
    settings = Settings()
    resolved_end_year = end_year or datetime.now(UTC).year
    engine = create_database_engine(settings.database_url)
    initialize_database(engine)
    session = create_session_factory(engine)()
    repository = MarketRepository(session)
    try:
        async with WorldBankClient(
            base_url=settings.world_bank_base_url,
            timeout_seconds=settings.request_timeout_seconds,
            retries=settings.request_retries,
        ) as source:
            return await run_pipeline(
                source=source,
                repository=repository,
                settings=settings,
                start_year=start_year,
                end_year=resolved_end_year,
            )
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    import asyncio

    asyncio.run(market_intelligence_flow())
