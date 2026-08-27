import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from market_intel.catalog import COUNTRIES
from market_intel.domain import IndicatorDefinition, ObservationRecord


class SourceContractError(ValueError):
    """Raised when the upstream API response does not match the documented contract."""


@dataclass(frozen=True)
class FetchResult:
    records: list[ObservationRecord]
    source_updated_at: str | None
    raw_payload: list[Any]


class IndicatorSource(Protocol):
    async def fetch_indicator(
        self, indicator: IndicatorDefinition, start_year: int, end_year: int
    ) -> FetchResult: ...


class WorldBankClient:
    def __init__(
        self,
        *,
        base_url: str = "https://api.worldbank.org/v2",
        timeout_seconds: float = 30,
        retries: int = 3,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.retries = retries
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            timeout=timeout_seconds,
            headers={"User-Agent": "latam-market-intelligence/1.0"},
        )

    async def __aenter__(self) -> "WorldBankClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def fetch_indicator(
        self, indicator: IndicatorDefinition, start_year: int, end_year: int
    ) -> FetchResult:
        country_path = ";".join(country.code for country in COUNTRIES)
        url = f"{self.base_url}/country/{country_path}/indicator/{indicator.code}"
        params = {
            "format": "json",
            "date": f"{start_year}:{end_year}",
            "per_page": "1000",
        }

        response: httpx.Response | None = None
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.retries + 1),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
            reraise=True,
        ):
            with attempt:
                response = await self.client.get(url, params=params)
                response.raise_for_status()

        if response is None:
            raise RuntimeError("request retry loop returned without a response")
        payload = response.json()
        return parse_world_bank_payload(payload, indicator)


def parse_world_bank_payload(payload: object, indicator: IndicatorDefinition) -> FetchResult:
    if not isinstance(payload, list) or len(payload) != 2:
        raise SourceContractError("expected a two-element World Bank API response")
    metadata, rows = payload
    if not isinstance(metadata, dict) or not isinstance(rows, list):
        raise SourceContractError("invalid metadata or records collection")

    source_updated_at = str(metadata.get("lastupdated")) if metadata.get("lastupdated") else None
    fetched_at = datetime.now(UTC)
    records: list[ObservationRecord] = []
    for row in rows:
        if not isinstance(row, dict) or row.get("value") is None:
            continue
        country = row.get("country")
        row_indicator = row.get("indicator")
        if not isinstance(country, dict) or not isinstance(row_indicator, dict):
            raise SourceContractError("record is missing country or indicator metadata")
        try:
            records.append(
                ObservationRecord(
                    country_code=str(row["countryiso3code"]),
                    country_name=str(country["value"]),
                    indicator_code=str(row_indicator["id"]),
                    indicator_name=str(row_indicator["value"]),
                    year=int(row["date"]),
                    value=float(row["value"]),
                    source_updated_at=source_updated_at,
                    fetched_at=fetched_at,
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SourceContractError(f"invalid observation record: {row!r}") from exc
    return FetchResult(records=records, source_updated_at=source_updated_at, raw_payload=payload)


class SnapshotSource:
    """Offline source backed by a committed snapshot of real World Bank responses."""

    def __init__(self, snapshot_path: Path) -> None:
        document = json.loads(snapshot_path.read_text(encoding="utf-8"))
        if not isinstance(document, dict) or not isinstance(document.get("indicators"), dict):
            raise SourceContractError("invalid snapshot document")
        self.document: dict[str, Any] = document

    async def fetch_indicator(
        self, indicator: IndicatorDefinition, start_year: int, end_year: int
    ) -> FetchResult:
        payload = self.document["indicators"].get(indicator.code)
        if payload is None:
            raise SourceContractError(f"snapshot does not contain {indicator.code}")
        parsed = parse_world_bank_payload(payload, indicator)
        records = [record for record in parsed.records if start_year <= record.year <= end_year]
        return FetchResult(
            records=records,
            source_updated_at=parsed.source_updated_at,
            raw_payload=payload,
        )
