# Repository Map

This repository is organized as a portfolio-friendly backend project: runnable, testable, and verifiable from public endpoints, while still keeping the deeper architecture notes in `docs/`.

## docs/

Public-safe documentation that explains intent and operational posture.

What belongs here:

- architecture and philosophy notes
- deployment and development guides
- observability/metrics guidance
- runbooks and repository navigation documents
- portfolio UX docs (recruiter quick start, screenshots, system topology)

What does not belong here:

- secrets (`.env` files, credentials, connection strings)
- private datasets or internal runbooks that assume privileged access

## src/

The production Python package: `lilith_replay_core`.

What belongs here:

- FastAPI app wiring and routes (`src/lilith_replay_core/api/`)
- deterministic primitives (validation, diffing)
- logging and observability primitives
- optional DB utilities used for connectivity checks

What does not belong here:

- ad-hoc scripts (use `scripts_public/`)
- test-only helpers (use `tests/`)

## tests/

Automated verification via `pytest`.

What belongs here:

- API tests (health, OpenAPI/Swagger availability, core endpoint behavior)
- deterministic behavior tests (diffing and validation)
- metrics smoke tests

What does not belong here:

- long-running integration suites that require private infrastructure
- fixtures containing private data

## scripts_public/

Standalone, public-safe utilities that can be run without starting the API server.

Examples:

- deterministic artifact diff helper
- replay manifest validator helper

Rule of thumb:

- scripts should not depend on internal infrastructure
- scripts should not require secrets

## examples/

Sample payloads and artifacts for quick manual testing and demos.

What belongs here:

- small CSV/JSON artifacts suitable for public commits
- example replay manifests (valid/invalid)

What does not belong here:

- production data, scraped data, or anything requiring redaction
