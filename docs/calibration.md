# Calibration (Public-Safe Notes)

This project includes calibration and validation experiments as part of an engineering learning process. The purpose is to make system behavior more measurable and stable over time, not to present “winning strategies.”

This document is intentionally public-safe:

- It does not include tuned thresholds, production selection logic, or calibrated artifacts.
- It does not include private datasets or deployment details.
- It avoids claims about profitability or performance.

## What “Calibration” Means Here

In Lilith, calibration refers to the practice of validating and adjusting probability-like outputs (or score-like signals) so that they behave consistently across time and conditions.

Examples of calibration concerns:

- A model score of X should correspond to similar empirical outcomes over time
- Drift should be detectable (the same score no longer means the same thing)
- Outputs should be interpretable in audits without relying on hidden constants

## Goals

- Improve interpretability of internal scores for audit and debugging
- Detect drift and instability across leagues/seasons/time windows
- Support safer governance: treat unstable or uncalibrated signals as advisory-only

## Non-Goals

- Publishing “best thresholds” or a final policy
- Claiming that calibration implies profitability
- Sharing trained artifacts derived from private data

## Calibration Workflow (Conceptual)

### 1) Define the Timestamped Training Window

- Calibration must respect time: fit using historical windows that end before the evaluation window.
- The system should record the training cutoff in a manifest.

### 2) Produce Reliability Evidence

Typical diagnostics (conceptual):

- Reliability curves / calibration plots
- Binning-based empirical rates over time windows
- Residual checks segmented by context (league, season, match state)

### 3) Apply a Calibrator (Optional)

Common calibrators (not prescriptive):

- Platt scaling (logistic)
- Isotonic regression
- Simple shrinkage toward a baseline in low-sample contexts

The public repo should describe the approach, not publish the learned parameters.

### 4) Lock and Audit

If calibration artifacts are used operationally (private):

- Store them immutably with version tags
- Record hashes and training cutoffs
- Fail closed if the expected artifact is missing or mismatched

In a public-safe repo, only the metadata patterns should be documented, not the artifacts themselves.

## Drift and Stability Checks

Calibration is not “set and forget.” Lilith treats drift as expected:

- Validate on rolling future windows (walk-forward)
- Monitor for context shifts and coverage changes
- Prefer conservative governance when drift is detected (e.g., shadow deployment, advisory-only)

## Public Repo Guidance

If you want to share calibration work publicly:

- Share schemas and plotting code structure, not trained outputs
- Keep examples synthetic or redacted
- Avoid any threshold tables or final decision rules
- Keep the focus on engineering hygiene: reproducibility, temporal correctness, and auditability

