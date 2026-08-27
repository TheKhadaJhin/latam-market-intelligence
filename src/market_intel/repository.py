import json
from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from market_intel.catalog import COUNTRIES, INDICATORS
from market_intel.domain import (
    ObservationRecord,
    PipelineResult,
    RunStatus,
    Scenario,
    ScoredMarket,
)
from market_intel.models import Country, Indicator, MarketScore, Observation, PipelineRun


class MarketRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def seed_catalog(self) -> None:
        for country in COUNTRIES:
            self.session.merge(Country(code=country.code, name=country.name, region=country.region))
        for indicator in INDICATORS:
            self.session.merge(
                Indicator(
                    code=indicator.code,
                    name=indicator.name,
                    unit=indicator.unit,
                    category=indicator.category,
                    polarity=indicator.polarity.value,
                    base_weight=indicator.base_weight,
                )
            )
        self.session.commit()

    def upsert_observations(self, records: Iterable[ObservationRecord]) -> int:
        count = 0
        for record in records:
            self.session.merge(
                Observation(
                    country_code=record.country_code,
                    indicator_code=record.indicator_code,
                    year=record.year,
                    value=record.value,
                    source_updated_at=record.source_updated_at,
                    fetched_at=record.fetched_at,
                )
            )
            count += 1
        self.session.commit()
        return count

    def list_observations(
        self,
        *,
        country_code: str | None = None,
        indicator_code: str | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> list[ObservationRecord]:
        statement = (
            select(Observation, Country.name, Indicator.name)
            .join(Country, Country.code == Observation.country_code)
            .join(Indicator, Indicator.code == Observation.indicator_code)
            .order_by(Observation.country_code, Observation.indicator_code, Observation.year)
        )
        if country_code:
            statement = statement.where(Observation.country_code == country_code.upper())
        if indicator_code:
            statement = statement.where(Observation.indicator_code == indicator_code)
        if start_year is not None:
            statement = statement.where(Observation.year >= start_year)
        if end_year is not None:
            statement = statement.where(Observation.year <= end_year)

        return [
            ObservationRecord(
                country_code=observation.country_code,
                country_name=country_name,
                indicator_code=observation.indicator_code,
                indicator_name=indicator_name,
                year=observation.year,
                value=observation.value,
                source_updated_at=observation.source_updated_at,
                fetched_at=observation.fetched_at,
            )
            for observation, country_name, indicator_name in self.session.execute(statement)
        ]

    def latest_observation_year(self) -> int | None:
        return self.session.scalar(select(func.max(Observation.year)))

    def replace_scores(
        self, reference_year: int, scenario: Scenario, scores: Iterable[ScoredMarket]
    ) -> int:
        self.session.execute(
            delete(MarketScore).where(
                MarketScore.reference_year == reference_year,
                MarketScore.scenario == scenario.value,
            )
        )
        count = 0
        for score in scores:
            self.session.add(
                MarketScore(
                    country_code=score.country_code,
                    reference_year=score.reference_year,
                    scenario=score.scenario.value,
                    overall_score=score.overall_score,
                    coverage_ratio=score.coverage_ratio,
                    rank=score.rank,
                    dimensions_json=json.dumps(score.dimensions, sort_keys=True),
                    indicator_scores_json=json.dumps(score.indicator_scores, sort_keys=True),
                    indicator_years_json=json.dumps(score.indicator_years, sort_keys=True),
                    calculated_at=score.calculated_at,
                )
            )
            count += 1
        self.session.commit()
        return count

    def get_scores(
        self, *, reference_year: int | None = None, scenario: Scenario = Scenario.BASE
    ) -> list[ScoredMarket]:
        year = reference_year
        if year is None:
            year = self.session.scalar(
                select(func.max(MarketScore.reference_year)).where(
                    MarketScore.scenario == scenario.value
                )
            )
        if year is None:
            return []

        statement = (
            select(MarketScore, Country.name)
            .join(Country, Country.code == MarketScore.country_code)
            .where(
                MarketScore.reference_year == year,
                MarketScore.scenario == scenario.value,
            )
            .order_by(MarketScore.rank)
        )
        return [
            ScoredMarket(
                country_code=score.country_code,
                country_name=country_name,
                reference_year=score.reference_year,
                scenario=Scenario(score.scenario),
                overall_score=score.overall_score,
                coverage_ratio=score.coverage_ratio,
                rank=score.rank,
                dimensions=json.loads(score.dimensions_json),
                indicator_scores=json.loads(score.indicator_scores_json),
                indicator_years=json.loads(score.indicator_years_json),
                calculated_at=score.calculated_at,
            )
            for score, country_name in self.session.execute(statement)
        ]

    def create_run(self, result: PipelineResult) -> None:
        self.session.add(
            PipelineRun(
                run_id=result.run_id,
                status=result.status.value,
                records_received=result.records_received,
                records_upserted=result.records_upserted,
                rankings_calculated=result.rankings_calculated,
                reference_year=result.reference_year,
                started_at=result.started_at,
                completed_at=result.completed_at,
                source_updated_at=result.source_updated_at,
                error=result.error,
            )
        )
        self.session.commit()

    def finish_run(self, result: PipelineResult) -> None:
        run = self.session.get(PipelineRun, result.run_id)
        if run is None:
            self.create_run(result)
            return
        run.status = result.status.value
        run.records_received = result.records_received
        run.records_upserted = result.records_upserted
        run.rankings_calculated = result.rankings_calculated
        run.reference_year = result.reference_year
        run.completed_at = result.completed_at
        run.source_updated_at = result.source_updated_at
        run.error = result.error
        self.session.commit()

    def list_runs(self, limit: int = 20) -> list[PipelineResult]:
        statement = select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(limit)
        return [
            PipelineResult(
                run_id=run.run_id,
                status=RunStatus(run.status),
                records_received=run.records_received,
                records_upserted=run.records_upserted,
                rankings_calculated=run.rankings_calculated,
                reference_year=run.reference_year,
                started_at=run.started_at,
                completed_at=run.completed_at,
                source_updated_at=run.source_updated_at,
                error=run.error,
            )
            for run in self.session.scalars(statement)
        ]

    def count_observations(self) -> int:
        return int(self.session.scalar(select(func.count()).select_from(Observation)) or 0)

    def latest_successful_run_at(self) -> datetime | None:
        return self.session.scalar(
            select(func.max(PipelineRun.completed_at)).where(
                PipelineRun.status == RunStatus.SUCCEEDED.value
            )
        )
