# Anti-Leakage and Temporal Validation

Lilith is designed around replayable decision cycles. That only works if replay runs enforce strict anti-leakage rules: the system must not “see the future” when producing an output at a historical timestamp.

This document describes the principles and validation patterns. It intentionally avoids thresholds, production selection logic, private datasets, and calibrated artifacts.

## Definitions

- **Leakage**: using information that would not have been available at decision time.
- **Temporal validation**: evaluating system behavior using time-ordered splits so future information cannot influence past decisions.
- **Replay timestamp**: the effective “now” for a replay run.

## Why Leakage Is Subtle

Leakage can enter a system even without explicitly reading outcomes:

- Aggregations computed over a full season that include matches after the replay timestamp
- Identity joins that rely on post-hoc corrected mappings
- Train/test splits that randomly shuffle time-ordered data
- Cached artifacts built using a later snapshot of the dataset

Lilith treats these as engineering problems, not just statistical ones.

## Anti-Leakage Principles

### 1) Time-Scoped Data Access

Every read should be conceptually scoped by a timestamp:

- “Give me the world as-of T”
- Not “give me the latest data we have”

If the system cannot guarantee the scope, it should fail closed rather than silently proceed.

### 2) Immutable Inputs for Replay

A replay run should use stable inputs:

- Snapshot files or versioned extracts where possible
- Run manifests that identify the exact input versions used

This enables reproducibility and makes audits meaningful.

### 3) Outcome Separation

Outcomes (labels) should be treated as a separate category of data:

- Allowed only for post-run settlement and evaluation
- Never used during decision assembly

### 4) Walk-Forward / Time-Ordered Validation

Validation should preserve the arrow of time:

- Fit on earlier windows
- Evaluate on later windows
- Repeat forward through time (walk-forward)

Random splits are useful for some debugging tasks, but they are not a substitute for temporal validation.

## Practical Leakage Controls

The public-safe controls Lilith aims for include:

- **Explicit cutoffs**: every feature/evidence layer has an “as-of” cutoff
- **Schema contracts**: decision-time schemas exclude fields that can contain outcomes
- **Audit checks**: automated assertions that decision inputs contain no post-event fields
- **Run manifests**: record timestamps, versions, and hashes of key inputs (excluding secrets)

## Validation Artifacts

To make anti-leakage verifiable, a run should produce:

- A manifest describing replay timestamp(s)
- A list of input sources and their as-of cutoffs
- A list of excluded fixtures/records and why
- A settlement/evaluation report generated after outcomes are known

These artifacts enable reviewers to confirm that the system’s decision-time view was consistent.

## Shadow Deployment as a Safety Valve

When changing infrastructure or adding evidence layers, shadow deployment helps reduce leakage risk:

- Run the full pipeline without external publishing
- Compare outputs across versions and timestamps
- Inspect audits for unexpected information pathways

## Public Repo Guidance

In a public repository, anti-leakage documentation should:

- Prefer principles, contracts, and example schemas
- Avoid listing tuned thresholds or production gating rules
- Avoid publishing calibration artifacts or any input datasets

