# Deterministic Artifact Diff (Public-Safe)

This note describes the philosophy and mechanics behind deterministic, audit-oriented diffs for replay/audit artifacts. It is written as an engineering design note: it focuses on reproducibility, stable ordering, and schema drift detection. It intentionally avoids prediction logic, tuned thresholds, private datasets, and operational endpoints.

Related:
- [replay_determinism.md](./replay_determinism.md)

## Why Deterministic Diffs Matter

Replay systems are only as useful as their comparability across runs.

- **Replay reproducibility**: rerunning the same replay with the same inputs should reproduce the same artifacts.
- **Audit reproducibility**: when two runs differ, reviewers should be able to explain the diff via provenance and contracts (schemas, hashes, ordering), without needing access to secrets.

Non-deterministic ordering (unstable row iteration, mixed timestamp formats, whitespace noise) produces “heisen-diffs”: diffs that change without any meaningful behavioral change. This damages confidence and makes debugging expensive.

Deterministic diffs address this by enforcing:
- Stable, deterministic ordering (columns and rows).
- Stable normalization (timestamps and whitespace).
- Stable hashing (canonical representations, consistent JSON encoding).

## Deterministic Diff Philosophy

A deterministic diff is designed to answer:

1) **Are these two artifacts equivalent under a stable normalization contract?**
2) **If not, what changed: schema, rows, or types?**
3) **Can the diff be reproduced exactly by another reviewer?**

This implies several design rules:

- **Fail closed on schema ambiguity**: if columns differ or types drift, treat it as schema drift (not “just a diff”).
- **Use canonical forms**: represent rows in a stable, canonical encoding and hash those encodings.
- **Prefer stable identifiers**: if a primary key exists, diff “by key” (added/removed/changed rows). If no key exists, fall back to multiset comparison (added/removed row hashes).
- **Keep output public-safe by default**: avoid printing raw row values; emit stable hashes and type fingerprints instead.

## Utility: deterministic_artifact_diff.py

The public-safe CLI utility lives at:
- [deterministic_artifact_diff.py](file:///c:/workspace_lilith/scripts_public/deterministic_artifact_diff.py)

It supports:
- CSV artifacts (header row + data rows).
- JSON artifacts (list of objects; or an object containing `rows` / `records` / `data` / `items`).

### What It Normalizes (Before Diffing)

1) **Column ordering**
- Uses the union of columns across left/right.
- Orders columns deterministically (lexicographic).
- Fills missing values as `null` for hashing/comparison.

2) **Row ordering**
- If a primary key is available (explicit or inferred), compares rows by key.
- Otherwise, compares as a multiset of row hashes.

3) **Timestamps**
- Normalizes ISO-like timestamps into a stable format.
- Timezone-aware timestamps are converted to UTC and represented as `...Z` with microsecond precision.

4) **Whitespace**
- Normalizes newlines and trims values.
- Collapses internal whitespace by default to reduce noise from formatting differences.

5) **Stable encoding + hashing**
- Canonical rows are encoded with sorted keys and stable JSON separators.
- The tool emits deterministic SHA-256 hashes for:
  - schema
  - normalized content

### What It Detects

- Added rows
- Removed rows
- Changed rows (when diffing by primary key)
- Schema differences (column additions/removals)
- Type inconsistencies (inferred type sets differ per column)

## Schema Drift Handling

Schema drift is treated as a distinct audit signal because it can conceal semantic changes even when headers look similar.

The utility marks **SCHEMA DRIFT** when any of the following occurs:
- Columns appear only on one side.
- Column type sets differ between left and right.

This is intentionally conservative: reviewers should not have to guess how to interpret a diff under shifting schema semantics.

## Artifact Lineage Validation (Stable Hashes)

For lineage inspection, the tool produces:
- `schema_sha256`: stable hash of the normalized schema contract.
- `content_sha256`: stable hash of the normalized row content (order-independent).

If both hashes match, the artifacts are equivalent under the normalization contract (PASS).

If the schema hashes differ, the artifact contracts differ (SCHEMA DRIFT).

If schema matches but content differs, the artifacts differ in rows (DIFF DETECTED).

## Audit-Oriented Debugging Workflow

A practical reviewer workflow:

1) Compare schema: are columns and inferred types consistent?
2) Compare hashes: do normalized schema/content hashes match?
3) Inspect row-level changes:
   - by primary key (preferred) to see “changed rows”
   - otherwise by row hash (added/removed)

This produces actionable diffs:
- schema drift (contract change)
- data drift (row-level change)
- normalization noise (e.g., timestamp/whitespace issues) minimized by design

## CLI Examples

Compare two CSV artifacts:

```bash
python scripts_public/deterministic_artifact_diff.py --left artifact_a.csv --right artifact_b.csv
```

Generate machine-readable JSON:

```bash
python scripts_public/deterministic_artifact_diff.py --left artifact_a.csv --right artifact_b.csv --json
```

Write JSON summary to a file:

```bash
python scripts_public/deterministic_artifact_diff.py --left artifact_a.csv --right artifact_b.csv --json-out diff_summary.json
```

Specify an explicit primary key:

```bash
python scripts_public/deterministic_artifact_diff.py --left artifact_a.csv --right artifact_b.csv --primary-key record_id
```

Disable normalization options (useful for diagnosing noise sources):

```bash
python scripts_public/deterministic_artifact_diff.py --left artifact_a.csv --right artifact_b.csv --no-collapse-whitespace --no-normalize-timestamps
```

## Deterministic Guarantees

Given identical normalized inputs, the utility guarantees:

- deterministic row hashing
- deterministic schema hashing
- stable ordering-independent comparison
- reproducible audit summaries
- replay-safe diff reproducibility

The utility intentionally avoids:
- probabilistic comparisons
- fuzzy matching
- heuristic row reconciliation
- non-deterministic output ordering

A diff that changes between runs without behavioral changes is treated as an integrity failure.

---

## Limitations

The utility is intentionally conservative.

It does not:
- infer semantic equivalence
- resolve fuzzy identity mappings
- reconcile structurally incompatible schemas
- perform domain-aware comparisons
- preserve ordering semantics unless explicitly configured

Schema ambiguity is treated as a validation problem rather than a recoverable warning.

---

## Notes on Public-Safe Output

By default, the utility avoids printing raw row values to reduce the risk of leaking private identifiers.

Row- and key-level information is represented as:
- deterministic SHA-256 hashes
- coarse type fingerprints (type + hash/length for non-primitive strings/structures)

If deeper inspection is needed, use the JSON output and correlate hashes to local artifacts under your own access controls.
