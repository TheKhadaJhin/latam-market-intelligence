# ADR 0001: World Bank Indicators as the initial source

- Status: Accepted
- Date: 2026-08-27

## Context

The first version needs real, comparable, license-documented data for six LATAM countries
without credentials or fragile scraping.

## Decision

Use the World Bank V2 Indicators API and retain a narrow committed snapshot for replay.

## Consequences

- Strong reproducibility and public documentation.
- Annual indicators are broad and delayed, so the product cannot represent real-time market
  conditions or local commercial details.
- Source attribution and upstream terms must remain visible.
