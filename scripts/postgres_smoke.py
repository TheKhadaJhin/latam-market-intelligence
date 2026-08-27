from sqlalchemy import func, select

from market_intel.config import Settings
from market_intel.database import create_database_engine, create_session_factory
from market_intel.models import MarketScore, Observation, PipelineRun


def main() -> None:
    engine = create_database_engine(Settings().database_url)
    session = create_session_factory(engine)()
    try:
        observations = session.scalar(select(func.count()).select_from(Observation))
        scores = session.scalar(select(func.count()).select_from(MarketScore))
        successful_runs = session.scalar(
            select(func.count()).select_from(PipelineRun).where(PipelineRun.status == "succeeded")
        )
        actual = (observations, scores, successful_runs)
        expected = (518, 18, 1)
        if actual != expected:
            raise RuntimeError(
                "PostgreSQL smoke test failed: "
                f"expected observations/scores/runs={expected}, found {actual}"
            )
        print("PostgreSQL smoke test passed: 518 observations, 18 scores, 1 successful run")
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()
