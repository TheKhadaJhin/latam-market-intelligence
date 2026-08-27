from collections.abc import Generator

from fastapi import Request

from market_intel.repository import MarketRepository


def get_repository(request: Request) -> Generator[MarketRepository, None, None]:
    session = request.app.state.session_factory()
    try:
        yield MarketRepository(session)
    finally:
        session.close()
