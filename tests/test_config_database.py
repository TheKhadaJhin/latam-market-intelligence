from pathlib import Path

import pytest

from market_intel.config import Settings, get_settings
from market_intel.database import create_database_engine, database_is_ready


def test_settings_parse_and_normalize_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MARKET_INTEL_ENVIRONMENT", "PRODUCTION")
    monkeypatch.setenv("MARKET_INTEL_CORS_ORIGINS", "https://one.test, https://two.test")
    monkeypatch.setenv("MARKET_INTEL_LOG_LEVEL", "warning")
    settings = Settings(_env_file=None)

    assert settings.is_production is True
    assert settings.cors_origins == ["https://one.test", "https://two.test"]
    assert settings.log_level == "WARNING"


@pytest.mark.parametrize(
    ("field", "value"),
    [("environment", "staging"), ("log_level", "TRACE")],
)
def test_settings_reject_invalid_values(field: str, value: str) -> None:
    with pytest.raises(ValueError):
        Settings(**{field: value})  # type: ignore[arg-type]


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()
    assert get_settings() is get_settings()
    get_settings.cache_clear()


def test_sqlite_engine_enables_readiness_and_foreign_keys(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'ready.db'}")
    try:
        assert database_is_ready(engine) is True
        with engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
    finally:
        engine.dispose()


def test_database_readiness_handles_connection_failure() -> None:
    engine = create_database_engine("sqlite:////missing-parent/data.db")
    try:
        assert database_is_ready(engine) is False
    finally:
        engine.dispose()
