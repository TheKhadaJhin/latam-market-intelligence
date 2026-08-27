# Methodology

## Purpose

The model offers a transparent comparison of the configured markets. It is designed to help
an analyst structure questions and identify trade-offs—not to produce a definitive expansion
decision.

## Indicator selection

Eight World Development Indicators cover four broad questions:

1. Is the economy growing and large enough to matter?
2. Are price and labor conditions comparatively stable?
3. Can a digital product reach an urban, connected population?
4. How connected is the economy to international trade?

Indicator definitions, units, polarity, categories, and weights are code-owned in
`src/market_intel/catalog.py` and exposed at `/v1/indicators`.

## Reference values and staleness

For each country and indicator, the model uses the latest non-null value at or before the
reference year. A value older than three years is rejected. No average, zero, or regional
value is silently substituted.

## Outliers and normalization

For each indicator:

1. Collect available cross-country values.
2. Calculate the 10th and 90th percentiles using linear interpolation.
3. Clip values to that interval.
4. Apply min-max normalization to `0–100`.
5. Reverse negative indicators so a higher normalized score always means a more favorable
   relative result.

If all values are equal, every available country receives `50` for that indicator.

## Coverage

Coverage is the sum of available scenario weights. Countries below 75% are excluded. For
included countries, weights are renormalized across available indicators and the overall
score is multiplied by:

```text
0.85 + (0.15 × coverage ratio)
```

This modest penalty keeps missing unfavorable observations from becoming an advantage while
still allowing comparisons when one lower-weight series is delayed.

## Scenarios

Weights always sum to `1.0`.

- **Base:** balanced lens.
- **Growth:** emphasizes GDP growth, internet adoption, and trade openness.
- **Resilience:** emphasizes inflation, unemployment, and GDP per capita.

Scenario differences are assumptions, not model-learned parameters. A professional decision
would include stakeholder review and sensitivity analysis before adoption.

## Interpretation

The result is relative only to the selected countries and data window. A score of `80` does
not mean a market is objectively “80% attractive.” It means its weighted, normalized
conditions compare favorably inside this configured peer set.

## Limitations

- Publication delays and revisions affect annual indicators.
- National averages hide subnational variation and market segments.
- Currency, regulatory, competitive, legal, product, and operational factors are incomplete.
- Correlated indicators may partially double-count related economic conditions.
- Weight changes can materially alter rankings.
- The model estimates no causal effect and provides no forecast.
