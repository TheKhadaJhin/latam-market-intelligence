from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from market_intel.database import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from market_intel.repository import MarketRepository


@pytest.fixture
def database(tmp_path: Path) -> Generator[tuple[Engine, MarketRepository], None, None]:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'test.db'}")
    initialize_database(engine)
    session: Session = create_session_factory(engine)()
    repository = MarketRepository(session)
    repository.seed_catalog()
    try:
        yield engine, repository
    finally:
        session.close()
        engine.dispose()
