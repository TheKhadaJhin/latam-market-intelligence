from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from market_intel.api.dependencies import get_repository
from market_intel.api.schemas import (
    CountryResponse,
    IndicatorResponse,
    MethodologyResponse,
    ObservationResponse,
    PipelineRunResponse,
    RankingResponse,
)
from market_intel.catalog import COUNTRIES, INDICATORS, SCENARIO_WEIGHTS
from market_intel.config import Settings
from market_intel.domain import Scenario
from market_intel.repository import MarketRepository

router = APIRouter(prefix="/v1")
RepositoryDependency = Annotated[MarketRepository, Depends(get_repository)]


@router.get("/countries", response_model=list[CountryResponse])
def list_countries() -> list[CountryResponse]:
    return [CountryResponse(**country.model_dump()) for country in COUNTRIES]


@router.get("/indicators", response_model=list[IndicatorResponse])
def list_indicators() -> list[IndicatorResponse]:
    return [
        IndicatorResponse(
            code=indicator.code,
            name=indicator.name,
            unit=indicator.unit,
            category=indicator.category,
            polarity=indicator.polarity.value,
            base_weight=indicator.base_weight,
        )
        for indicator in INDICATORS
    ]


@router.get("/rankings", response_model=list[RankingResponse])
def get_rankings(
    repository: RepositoryDependency,
    scenario: Scenario = Scenario.BASE,
    year: Annotated[int | None, Query(ge=1960, le=2100)] = None,
) -> list[RankingResponse]:
    scores = repository.get_scores(reference_year=year, scenario=scenario)
    if not scores:
        raise HTTPException(
            status_code=404,
            detail="No ranking is available. Run the pipeline or load the sample snapshot first.",
        )
    return [RankingResponse(**score.model_dump()) for score in scores]


@router.get("/countries/{country_code}/history", response_model=list[ObservationResponse])
def get_country_history(
    country_code: str,
    repository: RepositoryDependency,
    indicator: str | None = None,
    start_year: Annotated[int | None, Query(ge=1960, le=2100)] = None,
    end_year: Annotated[int | None, Query(ge=1960, le=2100)] = None,
) -> list[ObservationResponse]:
    normalized = country_code.upper()
    if normalized not in {country.code for country in COUNTRIES}:
        raise HTTPException(status_code=404, detail="Country is not in the configured market set.")
    if indicator and indicator not in {item.code for item in INDICATORS}:
        raise HTTPException(status_code=404, detail="Indicator is not in the configured catalog.")
    records = repository.list_observations(
        country_code=normalized,
        indicator_code=indicator,
        start_year=start_year,
        end_year=end_year,
    )
    return [
        ObservationResponse(
            country_code=record.country_code,
            country_name=record.country_name,
            indicator_code=record.indicator_code,
            indicator_name=record.indicator_name,
            year=record.year,
            value=record.value,
            source_updated_at=record.source_updated_at,
        )
        for record in records
    ]


@router.get("/pipeline-runs", response_model=list[PipelineRunResponse])
def list_pipeline_runs(
    repository: RepositoryDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[PipelineRunResponse]:
    return [PipelineRunResponse(**run.model_dump()) for run in repository.list_runs(limit)]


@router.get("/methodology", response_model=MethodologyResponse)
def get_methodology() -> MethodologyResponse:
    settings = Settings()
    return MethodologyResponse(
        version="1.0",
        normalization="Cross-country min-max normalization on the selected reference year.",
        outlier_treatment="Values are clipped to the 10th and 90th cross-country percentiles.",
        missing_data=(
            "The most recent value within the staleness window is used. Available weights are "
            "renormalized and a transparent coverage penalty is applied."
        ),
        minimum_coverage_ratio=settings.minimum_coverage_ratio,
        max_staleness_years=settings.max_staleness_years,
        scenarios={scenario.value: weights for scenario, weights in SCENARIO_WEIGHTS.items()},
        disclaimer=(
            "This portfolio model is an explainable comparison aid, not investment, legal, "
            "economic, or expansion advice."
        ),
    )
