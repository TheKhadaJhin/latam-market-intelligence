import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from market_intel.catalog import COUNTRIES, INDICATORS
from market_intel.config import Settings
from market_intel.services.world_bank import WorldBankClient


async def main() -> None:
    settings = Settings()
    destination = Path("data/sample/world_bank_snapshot.json")
    start_year = 2015
    end_year = datetime.now(UTC).year
    document: dict[str, object] = {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "source": "World Bank World Development Indicators API",
        "source_url": "https://api.worldbank.org/v2",
        "license": "CC BY 4.0 with World Bank additional dataset terms",
        "countries": [country.model_dump() for country in COUNTRIES],
        "start_year": start_year,
        "end_year": end_year,
        "indicators": {},
    }
    async with WorldBankClient(
        base_url=settings.world_bank_base_url,
        timeout_seconds=settings.request_timeout_seconds,
        retries=settings.request_retries,
    ) as source:
        for indicator in INDICATORS:
            result = await source.fetch_indicator(indicator, start_year, end_year)
            document["indicators"][indicator.code] = result.raw_payload  # type: ignore[index]
            print(f"{indicator.code}: {len(result.records)} observations")
    await asyncio.to_thread(destination.parent.mkdir, parents=True, exist_ok=True)
    await asyncio.to_thread(
        destination.write_text,
        json.dumps(document, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved reproducible snapshot to {destination}")


if __name__ == "__main__":
    asyncio.run(main())
