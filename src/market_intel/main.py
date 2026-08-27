import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import uuid4

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from market_intel import __version__
from market_intel.api.dependencies import get_repository
from market_intel.api.routes import router
from market_intel.api.schemas import HealthResponse, ReadinessResponse
from market_intel.config import Settings, get_settings
from market_intel.database import (
    create_database_engine,
    create_session_factory,
    database_is_ready,
    initialize_database,
)
from market_intel.logging import configure_logging
from market_intel.repository import MarketRepository

logger = structlog.get_logger()
REQUESTS = Counter(
    "market_intel_http_requests_total",
    "Total HTTP requests",
    labelnames=("method", "path", "status"),
)
LATENCY = Histogram(
    "market_intel_http_request_duration_seconds",
    "HTTP request duration in seconds",
    labelnames=("method", "path"),
)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    configure_logging(resolved.log_level, json_logs=resolved.is_production)
    app_engine = create_database_engine(resolved.database_url)
    session_factory = create_session_factory(app_engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        initialize_database(app_engine)
        app.state.engine = app_engine
        app.state.session_factory = session_factory
        app.state.settings = resolved
        logger.info("application_started", environment=resolved.environment)
        yield
        app_engine.dispose()
        logger.info("application_stopped")

    application = FastAPI(
        title="LATAM Market Intelligence API",
        version=__version__,
        description="Explainable market-comparison API backed by a reproducible data pipeline.",
        lifespan=lifespan,
        docs_url="/docs" if not resolved.is_production else None,
        redoc_url="/redoc" if not resolved.is_production else None,
    )
    application.state.engine = app_engine
    application.state.session_factory = session_factory
    application.state.settings = resolved
    application.add_middleware(GZipMiddleware, minimum_size=1000)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type", "X-Request-ID"],
    )

    @application.middleware("http")
    async def request_observability(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid4()))[:128]
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            REQUESTS.labels(request.method, request.url.path, "500").inc()
            logger.exception("request_failed", request_id=request_id, path=request.url.path)
            raise
        elapsed = time.perf_counter() - started
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        REQUESTS.labels(request.method, request.url.path, str(response.status_code)).inc()
        LATENCY.labels(request.method, request.url.path).observe(elapsed)
        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(elapsed * 1000, 2),
        )
        return response

    @application.get("/health", response_model=HealthResponse, tags=["operations"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="latam-market-intelligence", version=__version__)

    @application.get("/ready", response_model=ReadinessResponse, tags=["operations"])
    def readiness(
        repository: Annotated[MarketRepository, Depends(get_repository)],
    ) -> ReadinessResponse:
        database_ready = database_is_ready(app_engine)
        observations = repository.count_observations() if database_ready else 0
        response = ReadinessResponse(
            status="ready" if database_ready and observations > 0 else "not_ready",
            database=database_ready,
            observations=observations,
            last_successful_run_at=(
                repository.latest_successful_run_at() if database_ready else None
            ),
        )
        if response.status != "ready":
            raise HTTPException(status_code=503, detail=response.model_dump(mode="json"))
        return response

    @application.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    application.include_router(router)
    return application


app = create_app()
