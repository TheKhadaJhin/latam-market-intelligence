# syntax=docker/dockerfile:1.7
FROM python:3.15.0-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:0.11.33 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --create-home app

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
RUN uv sync --frozen --no-dev --extra postgres --extra dashboard --no-install-project && \
    uv sync --frozen --no-dev --extra postgres --extra dashboard

COPY alembic.ini ./
COPY migrations ./migrations
COPY dashboard ./dashboard
COPY data/sample ./data/sample

RUN mkdir -p /app/data/raw /app/data/exports && chown -R app:app /app
USER app

EXPOSE 8000
CMD ["uvicorn", "market_intel.main:app", "--host", "0.0.0.0", "--port", "8000"]
