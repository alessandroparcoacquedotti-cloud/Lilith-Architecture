# Lilith: Architecture (Public-Safe Overview)

Lilith is a replayable, event-driven decision system built primarily as a learning and validation project. This repository contains research tooling, a replay infrastructure, and audit-oriented outputs. It does not include the private datasets, deployment secrets, or production decision thresholds used in any operational environment.

Because this is my first serious software project, the documentation also reflects the learning process: mistakes, refactors, and design trade-offs are part of the repository scope.

This document focuses on engineering structure and validation philosophy rather than results.

## What This Project Is

- A self-taught, end-to-end software engineering project built over many iterations
- A replay-first system for running historical “as-if-live” decision cycles
- An experiment in governance: separating research from operational publishing and enforcing fail-closed behavior

## What This Project Is Not

- Not a betting guide and not financial advice
- Not a profitability claim or performance report
- Not a complete disclosure of production selection logic, thresholds, or calibrated artifacts

## System View (High Level)

At a high level, Lilith is organized around an event loop:

1. Ingest match/event inputs (historical or live-like feeds)
2. Normalize and map entities (teams, leagues, fixtures) into stable identifiers
3. Build “feature layers” and intermediate evidence artifacts
4. Apply decision gates to produce advisory outputs
5. Emit audit trails and replayable artifacts

The key idea is that steps (1)–(5) can run deterministically over historical timelines, enabling temporal validation without using future information.

## Repository Boundaries (Public-Safe)

This repo includes:

- Replay tooling and audit/report scaffolding
- Example output folder structure (redacted / placeholder)
- Engineering specs and notes about integrity, mapping, and validation

This repo excludes or intentionally redacts:

- Private/raw datasets and any provider-specific contracts
- Deployment secrets, tokens, credentials, and private endpoint configuration
- Final selection logic, decision thresholds, and calibrated model artifacts used in production

## Components

### Ingestion & Normalization

Purpose:

- Collect inputs (fixtures, teams, basic stats) and normalize them into consistent internal records
- Resolve entity identity and mitigate naming drift across sources

Key properties:

- Deterministic mappings where possible
- Strong integrity checks: reject or quarantine records that do not map cleanly

### Replay Engine

Purpose:

- Execute a historical day/time window using only information that would have been available at that time
- Produce outputs and audits that can be compared across code versions

Key properties:

- Time-aware data access (temporal cutoffs)
- Immutable replay inputs where feasible
- Machine-readable audit artifacts for later analysis

See [replay_engine.md](./replay_engine.md).

### Decision Layers (Redacted)

Lilith produces structured outputs from intermediate evidence. The public repository intentionally does not describe:

- The final selection policy
- Production gating thresholds or any tuned constants
- Operational ranking strategies

Instead, the docs focus on how decisions are governed, audited, and validated over time.

### Publishing / Operational Delivery (Governed)

When connected to an operational channel, Lilith uses a strict delivery-and-audit discipline:

- Emit a message payload (human-readable summary)
- Store delivery metadata (e.g., response code, message identifiers)
- Fail closed on delivery failures in live mode

Public docs describe the governance pattern, not the secrets or production endpoints.

See [governance.md](./governance.md).

## Fail-Closed Philosophy

Lilith is designed to “fail closed” in contexts where partial execution would create misleading outputs.

Examples of fail-closed behavior (high-level):

- Missing required upstream inputs → no outputs emitted
- Incomplete output bundle (e.g., missing metadata required for audit) → abort the run
- Delivery failures in live mode → treat as a run failure (not a silent success)

Fail-closed reduces the chance of quietly publishing un-auditable or inconsistent outputs.

## Observability & Audit Artifacts

Lilith emphasizes auditability over minimalism:

- Structured JSON/CSV outputs where possible
- Run manifests describing inputs and configuration hashes (without secrets)
- “Why” fields and trace identifiers to connect outputs back to evidence layers

The goal is to be able to answer: “What did the system know at the time, and why did it act?”

## Diagram

The architecture diagram is a placeholder in this public-safe structure:

- [architecture_diagram.png](../images/architecture_diagram.png)

In a public repo, the diagram should remain descriptive and avoid any operational endpoints, provider names, or private data flows.
