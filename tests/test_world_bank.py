import json
from pathlib import Path

import httpx
import pytest

from market_intel.catalog import INDICATORS
from market_intel.services.world_bank import (
    SnapshotSource,
    SourceContractError,
    WorldBankClient,
    parse_world_bank_payload,
)


def valid_payload() -> list[object]:
    return [
        {"page": 1, "pages": 1, "total": 2, "lastupdated": "2026-07-13"},
        [
            {
                "indicator": {"id": INDICATORS[0].code, "value": INDICATORS[0].name},
                "country": {"id": "AR", "value": "Argentina"},
                "countryiso3code": "ARG",
                "date": "2024",
                "value": 3.25,
            },
            {
                "indicator": {"id": INDICATORS[0].code, "value": INDICATORS[0].name},
                "country": {"id": "AR", "value": "Argentina"},
                "countryiso3code": "ARG",
                "date": "2023",
                "value": None,
            },
        ],
    ]


def test_parse_world_bank_payload_filters_nulls_and_maps_metadata() -> None:
    result = parse_world_bank_payload(valid_payload(), INDICATORS[0])

    assert result.source_updated_at == "2026-07-13"
    assert len(result.records) == 1
    assert result.records[0].country_code == "ARG"
    assert result.records[0].year == 2024
    assert result.records[0].value == 3.25


@pytest.mark.parametrize(
    "payload",
    [None, {}, [], [{}, {}], [{}, "not rows"], ["not metadata", []]],
)
def test_parse_world_bank_payload_rejects_contract_drift(payload: object) -> None:
    with pytest.raises(SourceContractError):
        parse_world_bank_payload(payload, INDICATORS[0])


def test_parse_world_bank_payload_rejects_invalid_record() -> None:
    payload = [{"lastupdated": "2026-01-01"}, [{"value": 1, "country": {}}]]
    with pytest.raises(SourceContractError):
        parse_world_bank_payload(payload, INDICATORS[0])


@pytest.mark.asyncio
async def test_world_bank_client_builds_request_and_retries_timeout() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ReadTimeout("temporary timeout", request=request)
        assert request.url.params["date"] == "2020:2024"
        assert request.url.params["format"] == "json"
        assert "ARG;BRA;CHL;COL;MEX;PER" in str(request.url)
        return httpx.Response(200, json=valid_payload())

    async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    source = WorldBankClient(retries=1, client=async_client)
    try:
        result = await source.fetch_indicator(INDICATORS[0], 2020, 2024)
    finally:
        await async_client.aclose()

    assert calls == 2
    assert len(result.records) == 1


@pytest.mark.asyncio
async def test_snapshot_source_filters_requested_years(tmp_path: Path) -> None:
    payload = valid_payload()
    payload[1][1]["value"] = 2.1  # type: ignore[index]
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps({"indicators": {INDICATORS[0].code: payload}}), encoding="utf-8")
    source = SnapshotSource(snapshot)

    result = await source.fetch_indicator(INDICATORS[0], 2023, 2023)

    assert [record.year for record in result.records] == [2023]


def test_snapshot_source_rejects_invalid_document(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text("[]", encoding="utf-8")
    with pytest.raises(SourceContractError):
        SnapshotSource(snapshot)
