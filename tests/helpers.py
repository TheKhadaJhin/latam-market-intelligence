from datetime import UTC, datetime

from market_intel.catalog import COUNTRIES, INDICATORS
from market_intel.domain import IndicatorDefinition, ObservationRecord
from market_intel.services.world_bank import FetchResult


def observation_records(year: int = 2024) -> list[ObservationRecord]:
    records: list[ObservationRecord] = []
    for country_index, country in enumerate(COUNTRIES, start=1):
        for indicator_index, indicator in enumerate(INDICATORS, start=1):
            value = float(country_index * 10 + indicator_index)
            if indicator.polarity.value == "negative":
                value = float((len(COUNTRIES) - country_index + 1) * 10 + indicator_index)
            records.append(
                ObservationRecord(
                    country_code=country.code,
                    country_name=country.name,
                    indicator_code=indicator.code,
                    indicator_name=indicator.name,
                    year=year,
                    value=value,
                    source_updated_at="2026-07-13",
                    fetched_at=datetime(2026, 8, 27, tzinfo=UTC),
                )
            )
    return records


class FakeSource:
    def __init__(self, *, fail: bool = False, year: int = 2024) -> None:
        self.fail = fail
        self.year = year

    async def fetch_indicator(
        self, indicator: IndicatorDefinition, start_year: int, end_year: int
    ) -> FetchResult:
        if self.fail:
            raise RuntimeError("upstream unavailable")
        records = [
            record
            for record in observation_records(self.year)
            if record.indicator_code == indicator.code and start_year <= record.year <= end_year
        ]
        return FetchResult(
            records=records,
            source_updated_at="2026-07-13",
            raw_payload=[
                {"lastupdated": "2026-07-13"},
                [{"indicator": indicator.code, "records": len(records)}],
            ],
        )
