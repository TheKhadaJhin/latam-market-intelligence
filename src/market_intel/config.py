from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MARKET_INTEL_",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = "development"
    database_url: str = "sqlite:///./data/market_intelligence.db"
    world_bank_base_url: str = "https://api.worldbank.org/v2"
    request_timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    request_retries: int = Field(default=3, ge=0, le=10)
    raw_data_dir: Path = Path("data/raw")
    api_key: str | None = None
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:8501",
        "http://localhost:3000",
    ]
    log_level: str = "INFO"
    max_staleness_years: int = Field(default=3, ge=0, le=10)
    minimum_coverage_ratio: float = Field(default=0.75, ge=0, le=1)

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        allowed = {"development", "test", "production"}
        normalized = value.lower()
        if normalized not in allowed:
            raise ValueError(f"environment must be one of {sorted(allowed)}")
        return normalized

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("invalid log level")
        return normalized

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str) and not value.lstrip().startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
