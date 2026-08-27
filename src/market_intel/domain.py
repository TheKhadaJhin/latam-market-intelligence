from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Polarity(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class Scenario(StrEnum):
    BASE = "base"
    GROWTH = "growth"
    RESILIENCE = "resilience"


class RunStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class CountryDefinition(BaseModel):
    code: str = Field(min_length=3, max_length=3)
    name: str
    region: str = "Latin America & Caribbean"

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.upper()


class IndicatorDefinition(BaseModel):
    code: str
    name: str
    unit: str
    category: str
    polarity: Polarity
    base_weight: float = Field(gt=0, le=1)


class ObservationRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    country_code: str
    country_name: str
    indicator_code: str
    indicator_name: str
    year: int = Field(ge=1960, le=2100)
    value: float
    source_updated_at: str | None = None
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        return value.upper()


class ScoredMarket(BaseModel):
    country_code: str
    country_name: str
    reference_year: int
    scenario: Scenario
    overall_score: float = Field(ge=0, le=100)
    coverage_ratio: float = Field(ge=0, le=1)
    rank: int = Field(gt=0)
    dimensions: dict[str, float]
    indicator_scores: dict[str, float]
    indicator_years: dict[str, int]
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PipelineResult(BaseModel):
    run_id: str
    status: RunStatus
    records_received: int = 0
    records_upserted: int = 0
    rankings_calculated: int = 0
    reference_year: int | None = None
    started_at: datetime
    completed_at: datetime | None = None
    source_updated_at: str | None = None
    error: str | None = None
