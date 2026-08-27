from market_intel.catalog import COUNTRIES, INDICATORS
from market_intel.domain import ObservationRecord, Scenario
from market_intel.services.scoring import _normalize, _quantile, calculate_scores
from tests.helpers import observation_records


def test_quantile_interpolates_and_rejects_empty_sequence() -> None:
    assert _quantile([0, 10], 0.25) == 2.5
    assert _quantile([7], 0.90) == 7

    try:
        _quantile([], 0.5)
    except ValueError as exc:
        assert "empty" in str(exc)
    else:
        raise AssertionError("empty quantiles must fail")


def test_normalize_handles_equal_values_and_negative_polarity() -> None:
    equal = _normalize({"ARG": 5, "BRA": 5}, INDICATORS[0].polarity)
    assert equal == {"ARG": 50.0, "BRA": 50.0}

    negative = _normalize({"ARG": 10, "BRA": 20}, INDICATORS[3].polarity)
    assert negative["ARG"] > negative["BRA"]
    assert _normalize({}, INDICATORS[0].polarity) == {}


def test_calculate_scores_ranks_all_markets_and_explains_dimensions() -> None:
    scores = calculate_scores(observation_records(), reference_year=2024, scenario=Scenario.BASE)

    assert len(scores) == len(COUNTRIES)
    assert [score.rank for score in scores] == list(range(1, len(COUNTRIES) + 1))
    assert all(score.coverage_ratio == 1 for score in scores)
    assert all(len(score.indicator_scores) == len(INDICATORS) for score in scores)
    assert all("growth" in score.dimensions for score in scores)
    assert scores[0].overall_score >= scores[-1].overall_score


def test_scenarios_change_weighted_results() -> None:
    records = []
    for record in observation_records():
        if record.country_code == "ARG" and record.indicator_code == "NY.GDP.MKTP.KD.ZG":
            record = record.model_copy(update={"value": 500.0})
        if record.country_code == "ARG" and record.indicator_code == "FP.CPI.TOTL.ZG":
            record = record.model_copy(update={"value": 500.0})
        records.append(record)
    base = calculate_scores(records, reference_year=2024, scenario=Scenario.BASE)
    growth = calculate_scores(records, reference_year=2024, scenario=Scenario.GROWTH)
    resilience = calculate_scores(records, reference_year=2024, scenario=Scenario.RESILIENCE)

    base_by_country = {item.country_code: item.overall_score for item in base}
    growth_by_country = {item.country_code: item.overall_score for item in growth}
    resilience_by_country = {item.country_code: item.overall_score for item in resilience}
    assert base_by_country != growth_by_country
    assert growth_by_country != resilience_by_country


def test_scoring_uses_latest_non_stale_value() -> None:
    records = observation_records(2022)
    recent = records[0].model_copy(update={"year": 2024, "value": 999.0})
    too_new = records[1].model_copy(update={"year": 2025, "value": 999.0})

    scores = calculate_scores([*records, recent, too_new], reference_year=2024)
    argentina = next(item for item in scores if item.country_code == "ARG")

    assert argentina.indicator_years[recent.indicator_code] == 2024
    assert argentina.indicator_years[too_new.indicator_code] == 2022


def test_scoring_excludes_country_below_weighted_coverage() -> None:
    records = [record for record in observation_records() if record.country_code != "ARG"]
    records.append(
        ObservationRecord(
            country_code="ARG",
            country_name="Argentina",
            indicator_code=INDICATORS[0].code,
            indicator_name=INDICATORS[0].name,
            year=2024,
            value=1,
        )
    )

    scores = calculate_scores(records, reference_year=2024, minimum_coverage_ratio=0.75)

    assert "ARG" not in {item.country_code for item in scores}
