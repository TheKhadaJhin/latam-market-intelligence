import json
from pathlib import Path

from market_intel.catalog import COUNTRIES, INDICATORS


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    snapshot_path = Path("data/sample/world_bank_snapshot.json")
    document = json.loads(snapshot_path.read_text(encoding="utf-8"))
    require(document["schema_version"] == "1.0", "Unexpected snapshot schema version")
    require(
        document["source"] == "World Bank World Development Indicators API",
        "Unexpected snapshot source",
    )
    require(len(document["countries"]) == len(COUNTRIES), "Unexpected country count")
    require(
        set(document["indicators"]) == {item.code for item in INDICATORS},
        "Snapshot indicator catalog does not match the application catalog",
    )
    observations = sum(
        sum(row.get("value") is not None for row in payload[1])
        for payload in document["indicators"].values()
    )
    require(observations == 518, f"Expected 518 observations, found {observations}")
    print(f"Snapshot contract passed: {observations} non-null observations")


if __name__ == "__main__":
    main()
