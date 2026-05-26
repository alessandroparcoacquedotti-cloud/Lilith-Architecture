# Governance

Lilith is not “just code that produces outputs.” The project is structured as an experiment in governance: how to make a decision system safer to iterate on by enforcing strict modes, auditability, and fail-closed behavior.

This documentation is intentionally public-safe. It avoids production thresholds, selection rules, calibrated artifacts, deployment secrets, and any private datasets.

## Why Governance Matters Here

This is my first serious programming project. As the project grew, it became clear that correctness and reproducibility required more than model tweaks:

- The system needs explicit operational modes
- Outputs must be auditable and attributable
- Missing data and delivery failures must be treated as failures, not “best effort”

Governance is how these constraints are enforced consistently.

## Operating Modes

Lilith supports distinct modes that change what the system is allowed to do:

- **Replay / Research**: runs historical windows for validation and analysis; no external publishing
- **Shadow Deployment**: runs the full pipeline but does not publish; captures the exact outputs and audits that would have been produced
- **Advisory-Only**: produces human-readable summaries for review; never treated as authoritative
- **Live Publishing** (private): allowed to deliver to an external channel; must fail closed on delivery issues

Public documentation focuses on the governance pattern rather than the operational wiring.

## Fail-Closed Philosophy

Fail-closed is the default stance: if the system cannot prove it is operating within its invariants, it should refuse to emit externally meaningful outputs.

Common invariants (high-level):

- Required upstream inputs exist and are internally consistent
- Output bundles include complete metadata needed for audit and later settlement analysis
- When publishing is enabled, delivery is confirmed and recorded

Fail-closed behavior prevents “silent degradation,” where the system keeps running but produces misleading or non-auditable results.

## Separation of Concerns

Governance is easier to enforce when modules are isolated:

- Data ingestion / normalization should not know about publishing
- Evidence building should be inspectable independent of decisions
- Publishing should operate only on validated output bundles

This separation makes it possible to run shadow deployments safely, and to replay historical windows without conflating research with operations.

## Audit Requirements

Every run should leave a trail that answers:

- What time window was executed?
- What inputs and versions were used (without secrets)?
- What outputs were produced and why?
- What failed, if anything, and at what step?

Public-safe audit artifacts typically include:

- Run manifest (timestamps, feature set identifiers, hashes)
- Coverage report (how many fixtures were eligible vs excluded)
- Failure reasons (machine-readable categories)
- Delivery metadata (when publishing is allowed), excluding tokens and endpoints

## Change Control (Lightweight)

Governance also includes how changes are made:

- Prefer small, replay-validated changes
- Maintain explicit “schema contracts” for outputs/audits
- Treat breaking changes to audit schemas as high-risk

The goal is not bureaucracy; it is to make iteration safe and explainable.

## Shadow Deployment

Shadow deployment means running the system end-to-end but preventing external effects:

- No messages sent to external channels
- Outputs recorded as if they were published
- Delivery step replaced by a no-op sink that still records intent

Shadow mode enables:

- Regression detection (outputs changed unexpectedly)
- Validation of new evidence layers or refactors
- Governance testing (fail-closed triggers exercised safely)

## Practical Guidance for a Public Repo

When sharing governance documentation publicly:

- Describe modes and invariants, not tuned parameters
- Use structural examples (schemas, manifests) rather than “best picks”
- Avoid references to private channels, provider endpoints, or credentials

