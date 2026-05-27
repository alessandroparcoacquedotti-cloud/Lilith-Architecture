# Replay Artifact Lineage (Deterministic, Auditable, Public-Safe)

This design note defines the replay artifact lineage model used by Lilith: what artifacts exist, how they relate, where determinism boundaries sit, and which validations must fail closed.

The goal is not “replay as a convenience feature”; the goal is replay as an integrity primitive:
a run can be reviewed, reproduced, and diffed without relying on implicit state.

This note intentionally avoids production decision logic, tuned thresholds, private datasets, and operational endpoints.

Related:
- [replay_determinism.md](./replay_determinism.md)
- [replay_engine.md](./replay_engine.md)
- [anti_leakage.md](./anti_leakage.md)
- Diagram: [replay_lineage_diagram.png](../images/replay_lineage_diagram.png)

---

## Model: Artifact Lineage as a First-Class Contract

Lilith treats the replay pipeline as a chain of immutable artifacts connected by explicit lineage identifiers.

A replay run is valid if:

- every decision-time artifact can be traced back to time-scoped inputs (“as-of `T`”)
- every artifact is attributable to exactly one replay manifest
- deterministic execution boundaries exist between stages
- contract violations abort the run (fail closed)

Lineage is implemented as an engineering discipline rather than a single storage feature.

The same principles apply whether artifacts are:
- JSON files
- CSV outputs
- database tables
- object store blobs

---

## Replay Artifact Lifecycle

The replay lifecycle is organized around seven artifact classes.

### 1) Raw Source (External / Upstream)

Definition:
- earliest representation of the world before normalization

Examples:
- provider feeds
- scraped pages
- API responses
- raw dumps

Constraints:
- raw sources are not assumed deterministic across time
- raw sources are not assumed stable unless snapshotted

Lineage requirement:
- replay must either snapshot raw sources or record provenance references

---

### 2) Ingestion Snapshot (As-Of `T`)

Definition:
- immutable snapshot representing “what existed as-of replay timestamp `T`”

Contract:
- scope is explicit
- identity resolution is validated
- snapshot becomes immutable once written

Required metadata:
- `as_of_timestamp`
- `source_fingerprint`
- `schema_version`
- `snapshot_id`

---

### 3) Feature Layer (Evidence) (As-Of `T`)

Definition:
- deterministic evidence computed strictly from inputs visible at `T`

Contract:
- feature visibility is frozen as-of `T`
- decision-time schemas exclude post-event fields
- computation must be deterministic or provenance-recorded

Required metadata:
- `as_of_timestamp`
- `input_snapshot_id`
- `layer_name`
- `layer_schema_version`
- `layer_fingerprint`

---

### 4) Replay Manifest (Run Root of Trust)

Definition:
- immutable declaration of the replay run identity and integrity

Contract:
- replay timestamps are immutable
- manifest is schema-validated before replay execution
- integrity metadata is mandatory

Public-safe enforcement example:
- [`replay_manifest_validator.py`](../scripts_public/replay_manifest_validator.py)

Required fields include:
- `run_id`
- `replay_timestamp`
- `fixtures_processed`
- `audit_schema_version`
- `integrity_hash`

---

### 5) Decision Artifact (Decision-Time Output)

Definition:
- decision-time output bundle emitted at replay timestamp `T`

Contract:
- derived only from evidence visible at `T`
- traceable back to evidence identifiers
- must not include outcomes or settlement data

Required metadata:
- `run_id`
- `replay_timestamp`
- `decision_schema_version`
- `evidence_references`
- `decision_fingerprint`

---

### 6) Audit Artifact (Diffable & Deterministic)

Definition:
- machine-readable artifacts explaining:
  - what the system knew
  - what it executed
  - why it proceeded or aborted

Contract:
- deterministic ordering
- stable schemas
- diff-friendly outputs
- audit readability without secrets

Public-safe examples:
- replay manifest validation
- deterministic ordering enforcement
- atomic write patterns
- fail-closed replay validation

Private orchestration and leak-guard implementations are intentionally excluded from this public repository.

---

### 7) Settlement Artifact (Post-Event Evaluation)

Definition:
- post-event evaluation artifacts generated only after outcomes exist

Examples:
- settlement reports
- evaluation summaries
- post-event analytics

Contract:
- settlement is downstream-only
- settlement must never mutate decision artifacts
- settlement outputs are isolated from replay evidence

Required metadata:
- `run_id`
- `settlement_as_of_timestamp`
- `decision_fingerprint`
- `settlement_schema_version`

---

## Immutable Replay Boundaries

Replay correctness depends on enforcing immutability at specific boundaries.

---

### Boundary A: As-Of Cutoff Boundary

Definition:
- boundary between data visible at `T` and data visible after `T`

Enforcement:
- explicit `as_of_timestamp`
- replay-scoped reads
- outcome separation by design

---

### Boundary B: Decision-Time vs Post-Event Boundary

Definition:
- boundary separating decision artifacts from settlement artifacts

Enforcement:
- settlement reads decision artifacts as immutable inputs
- settlement outputs become new artifacts
- mutation attempts are treated as lineage violations

---

### Boundary C: Deterministic Side-Effect Boundary

Definition:
- boundary between computation and persistence

Enforcement:
- atomic writes
- append-safe persistence
- deterministic ordering before writes
- replay-scoped namespaces

Public-safe examples:
- manifest validation
- deterministic replay ordering
- append-safe audit generation

---

## Validation Checkpoints (Fail-Closed)

Replay aborts when lineage or temporal correctness cannot be proven.

---

### 1) Timestamp Validation

Checks:
- timezone-aware ISO-8601 timestamps
- explicit clock semantics
- rejection of naive datetimes

Public-safe enforcement:
- [`replay_manifest_validator.py`](../scripts_public/replay_manifest_validator.py)

---

### 2) Schema Validation

Checks:
- artifact schema version validation
- schema drift detection
- deterministic schema contracts

---

### 3) Replay Manifest Integrity

Checks:
- required fields validation
- manifest integrity verification
- artifact-to-manifest attribution

Design rule:
- artifacts without lineage attribution are invalid replay artifacts

---

### 4) Feature Visibility Enforcement

Checks:
- evidence layers must contain only fields visible at `T`
- forbidden decision-time fields are rejected rather than ignored

Examples of forbidden fields:
- outcome labels
- settlement columns
- future-derived aggregates
- post-event metrics

Fail-closed behavior is preferred over partial replay continuation.

---

## Artifact Lineage Philosophy

### Reproducibility

Replay runs are intended to be rerunnable:

- same manifest
- same snapshots
- same code
- same replay timestamp

should produce identical outputs.

When upstream inputs are mutable:
- replay shifts toward audit reproducibility with explainable diffs and recorded provenance.

---

### Provenance

Provenance records:
- consumed inputs
- schema versions
- replay timestamps
- ordering rules
- artifact fingerprints

---

### Auditability

Audit artifacts should explain:
- what was processed
- what was excluded
- which invariants were enforced
- where replay aborted
- how artifacts link back to the replay manifest

---

### Deterministic Replay Tracking

Tracking is deterministic when:
- identifiers are stable
- ordering is explicit
- side effects are replay-scoped
- persistence boundaries are immutable

---

## Example Lineage Flows

### Flow 1: Minimal Replay

```text
Raw Source
  ↓
Ingestion Snapshot @ T
  ↓
Feature Layer(s) @ T
  ↓
Replay Manifest
  ↓
Decision Artifact @ T
  ↓
Audit Artifact(s)
  ↓
Settlement Artifact > T
```

---

### Flow 2: Multi-Day Replay

```text
for day in replay_window:
  seal manifest(day)
  snapshot(day, as_of=T_day)
  build features(day, cutoff=T_day)
  decide(day)
  audit(day)

after window:
  settle(day)
```

Critical property:
- day `N` evidence cannot mutate day `N-1` decisions.

---

### Flow 3: Fail-Closed Abort

```text
Forbidden post-event field detected
        ↓
Abort replay at evidence boundary
        ↓
Emit audit-only failure artifact
```

This preserves replay integrity:
- no decision artifact exists without defensible lineage.

---

## Architecture Diagram

The accompanying diagram shows:
- artifact classes
- lineage edges
- replay boundaries
- validation checkpoints
- deterministic execution flow

See:
- [replay_lineage_diagram.png](../images/replay_lineage_diagram.png)
