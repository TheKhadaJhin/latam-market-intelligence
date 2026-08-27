# ADR 0002: Explainable weighted scoring instead of machine learning

- Status: Accepted
- Date: 2026-08-27

## Context

There is no trustworthy labeled dataset of historical expansion decisions and outcomes.

## Decision

Use documented scenario weights, robust cross-country normalization, polarity, staleness,
coverage thresholds, and a small coverage penalty.

## Consequences

- Every score can be reconstructed and challenged.
- Rankings depend on analyst assumptions and peer-set composition.
- Weight sensitivity should be reviewed before real business use.
