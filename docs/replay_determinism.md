# Replay Determinism & Temporal Correctness

This note describes the determinism and temporal-correctness discipline behind Lilith’s replay engine. It is written as an engineering design note: it focuses on failure modes, invariants, and validation mechanics. It intentionally avoids production decision logic, tuned thresholds, private datasets, and operational endpoints.

Related docs:
- [replay_engine.md](./replay_engine.md)
- [anti_leakage.md](./anti_leakage.md)

## Problem Statement

The system is built around an “as-if-live” replay mode: take a historical window and execute the pipeline as if the replay timestamp were “now”, producing the same types of artifacts the live pipeline would produce (outputs plus audits), but without seeing future information.

Two properties are required for replay to be a meaningful validation tool:

- **Temporal correctness**: the pipeline must not consume any information that was not available as-of the replay timestamp.
- **Replay determinism**: given the same input snapshot, the same replay timestamp(s), and the same code, the pipeline should produce identical outputs and identical audit artifacts (or, if perfect determinism is impossible, produce a minimal, explainable diff with complete provenance recorded).

The remainder of this note treats replay as a security-style discipline: “future information” is an adversary and non-determinism is an integrity failure.

## Why Historical Replay Systems Fail

Most replay failures are not caused by an explicit `read_future_outcome()` call. They are caused by subtle coupling between decision-time computation and data that evolves after the fact.

### 1) Future Data Leakage (Direct and Indirect)

Leakage appears in multiple forms:

- **Direct leakage**: decision-time code reads outcomes, settlement fields, or post-event labels.
- **Indirect leakage**: decision-time code reads “safe looking” aggregates computed over a dataset that includes records after the replay timestamp (full-season summaries, “latest form”, rolling windows computed with an incorrect cutoff).
- **Join leakage**: identity resolution depends on mappings corrected post hoc; the mapping itself becomes future knowledge.

The signature is often “unreasonably stable” replay behavior: decisions appear too consistent because the pipeline is implicitly conditioned on information it should not have.

### 2) Post-Event Contamination

A replay run can contaminate itself if it mutates shared state across time boundaries:

- Cache entries (disk, memory, database) reused across days without being scoped by replay timestamp
- Upserts to “current state” tables that later days treat as ground truth
- Non-idempotent batch jobs writing to shared folders with unstable filenames (e.g., “latest.csv”)

Even if a single day is time-safe, cross-day mutation can accumulate into a “replay-only truth” that diverges from as-if-live behavior.

### 3) Recalculated Statistics

Many pipelines compute statistics “fresh” at replay time using today’s code and today’s datasets:

- Aggregates recomputed from a dataset that was backfilled or corrected later
- Derived features recomputed after schema changes, cleaning changes, or corrected identity joins
- “Best available” normalizers that silently change when data density changes

If recomputation is not bounded by an “as-of” cutoff and not tied to a versioned snapshot, replay becomes an unstable experiment: it answers “what would the system do today if it had always had today’s data”.

### 4) Hidden State Drift (Non-Determinism)

Even with correct temporal scoping, replay becomes non-comparable when it is not deterministic:

- Iteration over unordered containers (dict/set) without a stable sort
- Concurrency/race conditions that change merge order or last-write-wins behavior
- Random seeds not fixed (or fixed inconsistently across processes)
- Clock/timezone ambiguity: “now” leaks into the run through system time, local timezone, or file mtimes

This produces “heisen-diffs”: results change across runs for reasons unrelated to system behavior.

### 5) Timestamp Inconsistency

Replay systems often mix:

- Naive timestamps and timezone-aware timestamps
- Multiple clock domains (source timestamps, ingestion timestamps, decision timestamps)
- Ambiguous event ordering when timestamps collide (same-second, missing precision, inconsistent granularity)

When timestamp semantics are unclear, “as-of” rules become unenforceable: code cannot reliably decide what was known when.

## Replay Determinism Philosophy

Lilith’s replay discipline is based on a small set of non-negotiable ideas.

### “As-If-Live” Execution

Replay is not a separate pipeline that “simulates” live behavior. It is the live pipeline executed against historical time. The closer replay is to live execution order, the more useful it is:

- Same stages, same inputs (as-of), same artifact types, same audit contracts
- Separation between decision-time computation and post-run settlement/evaluation

### Immutable Replay Timestamps

Every replay decision is bound to a timestamp `T` that is treated as immutable:

- Data access is scoped “as-of `T`”
- “Now” is defined as `T`, not wall-clock time
- Output artifacts are labeled with `T` and derived from inputs visible at `T`

Timezone is part of correctness. The public-safe validator enforces ISO-8601 timestamps with explicit offsets (see [replay_manifest_validator.py](../scripts_public/replay_manifest_validator.py)).

### Deterministic Event Ordering

For any set of inputs, replay defines a deterministic ordering so identical inputs produce identical traversal:

- Stable ordering for fixtures/events (explicit sort keys, stable sort semantics)
- Stable ordering for stages (no data-dependent branching that reorders side effects)
- Deterministic tie-breakers when timestamps collide (e.g., `(event_time, provider_sequence, stable_id)` rather than relying on iteration order)

In code, this shows up as a preference for stable sorts (e.g., mergesort) and append-safe writes (see [live_orchestration_guard_utils.py](../scripts/live/live_orchestration_guard_utils.py)).

### Replay Reproducibility vs Audit Reproducibility

These are related but distinct:

- **Replay reproducibility**: rerunning the same replay with the same inputs produces the same outputs.
- **Audit reproducibility**: a reviewer can explain why a replay result differs across two runs by comparing manifests and provenance (inputs, schema versions, hashes), without needing access to secrets.

When upstream data cannot be perfectly frozen, audit reproducibility becomes the backstop: differences must be attributable, not mysterious.

## Replay Invariants

Replay determinism is enforced through invariants. Treat these as contracts: if an invariant is violated, the correct behavior is to abort (fail closed), not to “best effort” continue.

### Invariant Set (Design-Level)

1) **No future state access**

- Decision-time reads must be scoped by the replay timestamp `T`.
- Any attempt to read outcomes, settlement fields, or post-event labels during decision time is an integrity failure.

2) **Frozen feature visibility**

- Feature/evidence layers are built from inputs that are visible as-of `T`.
- The visibility cutoff is part of the artifact contract (the layer is “as-of” a timestamp), not an implicit assumption.

3) **Historical context isolation**

- Replay must not share mutable state across timestamps unless the state is explicitly versioned by timestamp.
- Caches, registries, and “current state” stores must be replay-scoped (keyed by `T` or by a replay run id).

4) **Deterministic execution boundaries**

- Inputs are enumerated deterministically and processed in a deterministic order.
- Side effects (artifact writes, upserts) occur in deterministic stages.
- Concurrency is allowed only if it cannot change observable results (or if it is strictly ordered at the boundary).

5) **Immutable replay manifests**

- A replay run emits a manifest that identifies the run id, replay timestamp, audit schema version, and an integrity hash.
- The manifest is treated as append-only: downstream artifacts are attributable to one manifest; a different manifest is a different run.

The public-safe validator encodes a minimal contract:

- Required fields include `run_id`, `replay_timestamp`, `fixtures_processed`, `audit_schema_version`, and `integrity_hash` (see [replay_manifest_validator.py](../scripts_public/replay_manifest_validator.py)).

### Why Invariants Matter

Replay without invariants fails silently. Silent failure is worse than loud failure because it creates confidence in a result that cannot be defended under review.

## Example Replay Lifecycle

This lifecycle describes the execution stages and the “time boundaries” where invariants are enforced. Concrete implementations vary by runner, but the stage boundaries are stable.

### Stage 0: Manifest Resolution (Seal the Run)

Inputs:
- Proposed replay timestamp(s) and selection criteria

Actions:
- Construct or load the replay manifest
- Validate manifest shape and timestamp semantics
- Bind the run id and the replay timestamp(s)

Outputs:
- A validated manifest object (the run’s root of trust)

Failure cases:
- Missing required manifest fields
- Timestamp missing timezone offset or invalid ISO-8601 format

### Stage 1: Universe Selection (What Exists at T)

Inputs:
- Manifest `T`
- Fixture/event inventory as-of `T`

Actions:
- Determine the replay universe (fixtures/events eligible for processing)
- Validate stable identity resolution and required joins
- Produce a deterministic ordering for the universe

Outputs:
- Ordered, immutable list of replay targets for `T`

Failure cases:
- Missing identity mapping (fail closed instead of guessing)
- Non-deterministic universe ordering (e.g., relying on file iteration order)

### Stage 2: Evidence Assembly (Build “What the System Knows at T”)

Inputs:
- Ordered replay targets
- Source artifacts visible as-of `T`

Actions:
- Build evidence layers with explicit cutoffs
- Ensure decision-time schemas exclude post-event and outcome fields
- Persist evidence artifacts using atomic writes

Outputs:
- Evidence bundle labeled as-of `T` with schema versions

Failure cases:
- Evidence includes forbidden fields (odds/EV/probability, outcomes, settlement columns)
- Evidence layer cannot assert its cutoff/provenance

### Stage 3: Decision Assembly (Redacted Policy Boundary)

Inputs:
- Evidence bundle for `T`

Actions:
- Assemble decisions from evidence
- Emit structured outputs with traceability back to evidence ids

Outputs:
- Output bundle for `T` plus audit summaries

Failure cases:
- Required evidence missing or inconsistent with schema contract
- Output bundle incomplete (auditing would be ambiguous)

### Stage 4: Post-Run Settlement / Evaluation (After the Arrow of Time)

Inputs:
- Outputs emitted at `T`
- Outcomes that become available after events conclude

Actions:
- Compute evaluation/settlement artifacts
- Record post-event metrics separately from decision-time artifacts

Outputs:
- Settlement report that never feeds back into decision-time computation for earlier timestamps

Failure cases:
- Settlement artifacts mixed into decision-time evidence storage

### A Concrete Flow (Text Diagram)

```text
            +-------------------+
            |  Stage 0          |
            |  Manifest sealed  |
            +---------+---------+
                      |
                      v
            +-------------------+
            |  Stage 1          |
            |  Universe @ T     |
            +---------+---------+
                      |
                      v
            +-------------------+
            |  Stage 2          |
            |  Evidence @ T     |
            +---------+---------+
                      |
                      v
            +-------------------+
            |  Stage 3          |
            |  Decision @ T     |
            +---------+---------+
                      |
                      v
            +-------------------+
            |  Stage 4          |
            |  Settlement > T   |
            +-------------------+
```

The important technical point is the boundary: Stage 4 is “after time” and is not allowed to mutate Stage 2/3 artifacts for the same run.

## Replay Abort Examples (Fail-Closed Validation)

The system prefers aborting a replay run over emitting partial artifacts that cannot be trusted. Examples below are intentionally generic (no thresholds, no operational endpoints).

### Abort: Manifest Timestamp Ambiguous

Condition:
- `replay_timestamp` is missing timezone information (naive datetime)

Outcome:
- Abort at Stage 0 with a schema error

Where enforced:
- [replay_manifest_validator.py](../scripts_public/replay_manifest_validator.py) requires timezone-aware ISO-8601 timestamps.

### Abort: Forbidden Fields in Decision-Time Data

Condition:
- A decision-time dataframe includes columns that should not exist in the decision schema (examples: “odds”, “expected_value”, “probability”)

Outcome:
- Abort at evidence assembly rather than trying to ignore columns

Where enforced (example pattern):
- A leak-guard rejects these fields and raises an error (“Fail closed.”). One instance is in [lilith_full_season_replay_as_live_validator_v1.py](../scripts/audit/lilith_full_season_replay_as_live_validator_v1.py).

### Abort: Non-Deterministic Ordering at a Boundary

Condition:
- Replay universe iteration order changes between runs while inputs are unchanged (e.g., filesystem order or hash-randomized dict ordering is used)

Outcome:
- Abort or mark run invalid; deterministic ordering must be explicit

Engineering note:
- If the boundary write is append-safe but the ordering is unstable, you can get “valid-looking” artifacts whose internal row order changes. That is still a determinism failure for diff-based review.

### Abort: Post-Event Contamination Detected

Condition:
- A run detects that evidence artifacts for `T` were overwritten by a later step (or by another run) rather than written as immutable outputs

Outcome:
- Abort (or quarantine) because provenance is broken

Mitigation pattern:
- Use atomic writes and stable naming derived from replay manifest identifiers (see [live_orchestration_guard_utils.py](../scripts/live/live_orchestration_guard_utils.py)).

### Abort: Audit Schema Mismatch

Condition:
- The replay runner emits an audit artifact that does not match the declared `audit_schema_version`

Outcome:
- Abort; downstream readers must not guess field meanings

Reason:
- Schema drift is a determinism failure because “same-looking CSV headers” can conceal semantic changes.

## Deterministic Validation Guarantees

Replay determinism is not a slogan; it is a set of guarantees with explicit assumptions.

### What the System Can Guarantee

Given:
- A validated replay manifest (including immutable timestamps)
- Versioned or hash-identified input artifacts
- A fixed code version and a controlled runtime environment

Then replay can guarantee:

- **Temporal isolation**: decision-time artifacts do not incorporate post-event fields, labels, or settlement data.
- **Stable ordering at boundaries**: replay targets and emitted artifacts have deterministic ordering and stable tie-breakers.
- **Artifact integrity**: manifests and audit artifacts can be cross-checked by schema versions and integrity hashes.
- **Fail-closed behavior**: invariant violations stop the run rather than producing ambiguous partial outputs.

### What the System Does Not Guarantee (And How It Compensates)

Some sources are inherently mutable in a public repository context (upstream feeds, backfilled datasets, corrected mappings). When perfect freezing is not feasible:

- Replay shifts emphasis to **audit reproducibility**: the run records enough provenance to explain diffs.
- A run is treated as a distinct experiment when its manifest or input hashes differ, even if the replay timestamp is the same.

### Practical Review Workflow (Diff-Oriented)

Determinism is operationally useful when a reviewer can do this:

1) Compare manifests: timestamps, schema versions, integrity hashes.
2) Diff evidence artifacts and output bundles for a fixed `T`.
3) If a diff exists, attribute it to either:
   - an intentional code change (expected), or
   - an input/provenance change (recorded), or
   - a determinism violation (bug).

The goal is to make the third category small and actionable.

