# Releases

This repository uses Semantic Versioning as a baseline.

This document is intentionally short and portfolio-oriented: it highlights verifiable milestones and the engineering surface area that changed between releases.

## v0.1.0 (released)

Major milestones:

- API: public-safe FastAPI service with Swagger (`/docs`) and OpenAPI (`/openapi.json`)
- Prometheus: metrics endpoint (`/metrics`) and low-cardinality metric labels
- Public health endpoints: `/health` and `/health/db` (DB check is safe/fail-closed and does not leak secrets)
- Developer workflow: Ruff, Mypy, Pytest, CI, Dockerfile, Docker Compose, Railway/Render config

## v0.2.0 (planned)

Major milestones:

- PostgreSQL: first-class “Postgres-ready” local/deployment workflow with consistent connectivity verification
- Persistence: database-backed lineage/audit primitives (store replay runs and artifact records, expose lineage reads)
- Prometheus: expanded, stable metric surface for replay and lineage workflows
- Grafana: published dashboard export (JSON) and a minimal “how to import” operator note

