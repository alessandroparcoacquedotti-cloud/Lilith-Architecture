# Replay Engine

Lilith is built around the ability to replay historical days as if they were being processed live. This is primarily an engineering and validation tool: it allows deterministic experiments, temporal checks, and audit-driven iteration without relying on real-time operations.

This document describes the replay concept and its safety constraints. It intentionally does not disclose production decision logic, thresholds, private datasets, or calibrated artifacts.

## Goals

- Make runs reproducible and comparable across code versions
- Enforce temporal correctness (no future information)
- Produce auditable, machine-readable artifacts (inputs, decisions, delivery metadata)
- Support “shadow” execution paths that do not publish externally

## Non-Goals

- Not a public performance or profitability report
- Not an attempt to recreate operational performance claims
- Not a public specification of production policies or thresholds

## Core Idea: Replay-as-Live

Replay-as-live means treating a historical time window as the “present”:

- Inputs are restricted to what would have been available by the replay timestamp
- Outcomes and post-match fields are excluded during decision time
- The same run produces the same results given the same inputs and code

This makes it possible to test governance and infrastructure changes without contaminating the decision timeline.

## Temporal Data Access Rules (Anti-Leakage)

At decision time, a replay run must only access:

- Pre-match metadata (fixture identity, kickoff time, participants)
- Pre-match evidence layers computed from historical data that ends before the decision timestamp

A replay run must not access:

- Match outcomes (final score, result) before the match concludes
- Any post-event labels used for training or calibration
- Any feature that implicitly encodes outcomes (e.g., “form” computed using matches after the timestamp)

See [anti_leakage.md](./anti_leakage.md).

## Typical Replay Flow

### 1) Select a Replay Window

- Define a date range (or daily batch)
- Define a “decision timestamp” for each match or cycle

### 2) Resolve Fixtures and Stable Identity

- Map external team/league naming into internal identifiers
- Validate that identities are stable and complete
- Fail closed if core identity mapping is incomplete

### 3) Build Evidence Layers

Lilith uses intermediate artifacts to separate:

- Data normalization and integrity checks
- Feature extraction / evidence building
- Decision gating and output assembly

Public documentation describes the separation of layers, not the final decision policy.

### 4) Decision Gating (Redacted)

The system consumes evidence layers and produces:

- Advisory outputs suitable for replay and audit
- Internal run diagnostics

The public repo intentionally avoids documenting final selection logic and thresholds.

### 5) Emit Replay Outputs and Audits

Replay outputs are designed to be inspected and diffed:

- Run manifest (inputs + environment summary, excluding secrets)
- Output bundle (structured picks/advisories, with metadata)
- Audit trails (coverage, integrity checks, failure reasons)

## Determinism and Reproducibility

Replay runs aim to be deterministic:

- Explicit input snapshots where possible
- Stable ordering when iterating over fixtures
- Versioned run manifests for later comparison

When true determinism is not feasible (e.g., upstream data changes), the system should record enough metadata to explain differences.

## Fail-Closed in Replay

Replay mode should still fail closed when invariants are broken, because silent partial success makes validation unreliable.

Examples (high-level):

- Missing core fixture identity → abort that cycle/run
- Incomplete evidence bundle required by downstream output assembly → abort
- Audit schema mismatch → abort (prevents “unknown unknowns”)

## Output Examples (Public-Safe)

The repository includes placeholder folders intended to hold redacted samples:

- [examples/replay_outputs](../examples/replay_outputs)
- [examples/audit_examples](../examples/audit_examples)

Any public examples should:

- Remove private datasets and provider identifiers
- Avoid thresholds and tuned constants
- Prefer structural examples (schemas, manifests, trace IDs) over “what to pick”
