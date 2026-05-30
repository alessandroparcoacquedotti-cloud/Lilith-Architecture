# Philosophy

This repository is built around deterministic replay, audit-oriented engineering, and a fail-closed posture. The aim is a public-safe platform that can validate and compare replay artifacts without exposing sensitive internals.

## Future Information as an Adversary

In validation and governance settings, future information can leak into systems via timestamps, joins, and backfilled fields. A replay system must reconstruct what was known at a point in time and surface contamination as drift.

## Deterministic Replay Philosophy

Deterministic replay means:

- the same inputs produce the same validated outputs
- normalization rules are explicit and stable
- comparisons use deterministic hashing and stable summaries

## Fail-Closed Systems

Fail-closed posture means:

- prefer explicit errors over misleading success
- avoid silent coercion of malformed inputs
- keep error responses consistent and public-safe

## Audit-Oriented Engineering

Audit-oriented engineering optimizes for traceability and reproducibility:

- request correlation via `request_id`
- replay correlation via `replay_run_id`
- public-safe summaries over raw artifact logging

## Public-Safe Boundaries

This repository must not expose:

- prediction logic
- betting logic
- private datasets
- operational thresholds
- secrets
