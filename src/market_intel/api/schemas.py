from datetime import datetime

from pydantic import BaseModel, Field

from market_intel.domain import RunStatus, Scenario


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadinessResponse(BaseModel):
    status: str
    database: bool
    observations: int
    last_successful_run_at: datetime | None


class CountryResponse(BaseModel):
    code: str
    name: str
    region: str


class IndicatorResponse(BaseModel):
    code: str
    name: str
    unit: str
    category: str
    polarity: str
    base_weight: float


class RankingResponse(BaseModel):
    country_code: str
    country_name: str
    reference_year: int
    scenario: Scenario
    overall_score: float
    coverage_ratio: float
    rank: int
    dimensions: dict[str, float]
    indicator_scores: dict[str, float]
    indicator_years: dict[str, int]
    calculated_at: datetime


class ObservationResponse(BaseModel):
    country_code: str
    country_name: str
    indicator_code: str
    indicator_name: str
    year: int
    value: float
    source_updated_at: str | None


class PipelineRunResponse(BaseModel):
    run_id: str
    status: RunStatus
    records_received: int
    records_upserted: int
    rankings_calculated: int
    reference_year: int | None
    started_at: datetime
    completed_at: datetime | None
    source_updated_at: str | None
    error: str | None


class MethodologyResponse(BaseModel):
    version: str
    normalization: str
    outlier_treatment: str
    missing_data: str
    minimum_coverage_ratio: float = Field(ge=0, le=1)
    max_staleness_years: int
    scenarios: dict[str, dict[str, float]]
    disclaimer: str
