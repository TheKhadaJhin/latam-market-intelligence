import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

from market_intel.config import Settings
from market_intel.main import create_app
from market_intel.repository import MarketRepository
from market_intel.services.pipeline import run_pipeline
from tests.helpers import FakeSource


def test_health_readiness_metrics_and_security_headers(tmp_path: Path) -> None:
    settings = Settings(
        environment="test",
        database_url=f"sqlite:///{tmp_path / 'api.db'}",
        raw_data_dir=tmp_path / "raw",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        health = client.get("/health", headers={"X-Request-ID": "test-request"})
        assert health.status_code == 200
        assert health.json()["version"] == "1.0.0"
        assert health.headers["X-Request-ID"] == "test-request"
        assert health.headers["X-Content-Type-Options"] == "nosniff"
        assert client.get("/ready").status_code == 503
        metrics = client.get("/metrics")
        assert metrics.status_code == 200
        assert "market_intel_http_requests_total" in metrics.text


def test_read_api_after_pipeline_and_validation_errors(tmp_path: Path) -> None:
    settings = Settings(
        environment="test",
        database_url=f"sqlite:///{tmp_path / 'populated.db'}",
        raw_data_dir=tmp_path / "raw",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        session = app.state.session_factory()
        repository = MarketRepository(session)
        try:
            asyncio.run(
                run_pipeline(
                    source=FakeSource(),
                    repository=repository,
                    settings=settings,
                    start_year=2020,
                    end_year=2024,
                    persist_raw=False,
                )
            )
        finally:
            session.close()

        ready = client.get("/ready")
        assert ready.status_code == 200
        assert ready.json()["observations"] == 48

        assert len(client.get("/v1/countries").json()) == 6
        assert len(client.get("/v1/indicators").json()) == 8
        rankings = client.get("/v1/rankings", params={"scenario": "growth"})
        assert rankings.status_code == 200
        assert len(rankings.json()) == 6
        assert rankings.json()[0]["rank"] == 1

        history = client.get(
            "/v1/countries/arg/history",
            params={"indicator": "NY.GDP.MKTP.KD.ZG"},
        )
        assert history.status_code == 200
        assert len(history.json()) == 1
        assert len(client.get("/v1/pipeline-runs", params={"limit": 1}).json()) == 1
        methodology = client.get("/v1/methodology")
        assert methodology.status_code == 200
        assert set(methodology.json()["scenarios"]) == {"base", "growth", "resilience"}

        assert client.get("/v1/countries/USA/history").status_code == 404
        assert (
            client.get("/v1/countries/ARG/history", params={"indicator": "unknown"}).status_code
            == 404
        )
        assert client.get("/v1/rankings", params={"year": 1990}).status_code == 404
        assert client.get("/v1/pipeline-runs", params={"limit": 0}).status_code == 422


def test_production_disables_interactive_api_docs(tmp_path: Path) -> None:
    app = create_app(
        Settings(environment="production", database_url=f"sqlite:///{tmp_path / 'prod.db'}")
    )
    with TestClient(app) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/redoc").status_code == 404
