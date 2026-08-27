from collections import defaultdict
from collections.abc import Iterable, Sequence

from market_intel.catalog import COUNTRIES, INDICATORS, SCENARIO_WEIGHTS
from market_intel.domain import ObservationRecord, Polarity, Scenario, ScoredMarket


def _quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("cannot calculate a quantile for an empty sequence")
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _normalize(values: dict[str, float], polarity: Polarity) -> dict[str, float]:
    if not values:
        return {}
    raw_values = list(values.values())
    lower = _quantile(raw_values, 0.10)
    upper = _quantile(raw_values, 0.90)
    if abs(upper - lower) < 1e-12:
        return {country: 50.0 for country in values}

    normalized: dict[str, float] = {}
    for country, value in values.items():
        clipped = min(max(value, lower), upper)
        score = (clipped - lower) / (upper - lower) * 100
        if polarity == Polarity.NEGATIVE:
            score = 100 - score
        normalized[country] = round(score, 4)
    return normalized


def calculate_scores(
    observations: Iterable[ObservationRecord],
    *,
    reference_year: int,
    scenario: Scenario = Scenario.BASE,
    max_staleness_years: int = 3,
    minimum_coverage_ratio: float = 0.75,
) -> list[ScoredMarket]:
    """Calculate explainable cross-country scores using robust min-max normalization.

    Values are clipped at the cross-country 10th and 90th percentiles. Missing indicators
    are allowed up to the coverage threshold, while a small coverage penalty prevents sparse
    markets from outranking complete ones solely due to missing unfavorable indicators.
    """

    latest: dict[tuple[str, str], ObservationRecord] = {}
    earliest_allowed = reference_year - max_staleness_years
    for record in observations:
        if not earliest_allowed <= record.year <= reference_year:
            continue
        key = (record.country_code, record.indicator_code)
        current = latest.get(key)
        if current is None or record.year > current.year:
            latest[key] = record

    definitions = {item.code: item for item in INDICATORS}
    country_names = {item.code: item.name for item in COUNTRIES}
    weights = SCENARIO_WEIGHTS[scenario]
    indicator_scores: dict[str, dict[str, float]] = {}

    for indicator_code, definition in definitions.items():
        values = {
            country_code: record.value
            for (country_code, code), record in latest.items()
            if code == indicator_code
        }
        indicator_scores[indicator_code] = _normalize(values, definition.polarity)

    provisional: list[ScoredMarket] = []
    for country_code, country_name in country_names.items():
        available = {
            code: scores[country_code]
            for code, scores in indicator_scores.items()
            if country_code in scores
        }
        available_weight = sum(weights[code] for code in available)
        coverage_ratio = available_weight / sum(weights.values())
        if coverage_ratio + 1e-12 < minimum_coverage_ratio:
            continue

        weighted_score = sum(available[code] * weights[code] for code in available)
        weighted_score /= available_weight
        coverage_penalty = 0.85 + 0.15 * coverage_ratio
        overall = max(0.0, min(100.0, weighted_score * coverage_penalty))

        dimension_values: dict[str, list[tuple[float, float]]] = defaultdict(list)
        for code, score in available.items():
            dimension_values[definitions[code].category].append((score, weights[code]))
        dimensions = {
            category: round(
                sum(score * weight for score, weight in items) / sum(weight for _, weight in items),
                2,
            )
            for category, items in dimension_values.items()
        }
        years = {
            code: latest[(country_code, code)].year
            for code in available
            if (country_code, code) in latest
        }
        provisional.append(
            ScoredMarket(
                country_code=country_code,
                country_name=country_name,
                reference_year=reference_year,
                scenario=scenario,
                overall_score=round(overall, 2),
                coverage_ratio=round(coverage_ratio, 4),
                rank=1,
                dimensions=dimensions,
                indicator_scores={code: round(score, 2) for code, score in available.items()},
                indicator_years=years,
            )
        )

    provisional.sort(key=lambda item: (-item.overall_score, item.country_code))
    return [item.model_copy(update={"rank": rank}) for rank, item in enumerate(provisional, 1)]
