# RELEASE AUDIT — v0.2.0

Scope: documentation and release verification only. No application behavior changes.

## Version Consistency

Expected release version: `0.2.0`

Verified version references:

- Package version: [pyproject.toml](file:///c:/workspace_lilith_public/_repo_clone/pyproject.toml#L5-L8) → `0.2.0`
- Runtime version constant: [__init__.py](file:///c:/workspace_lilith_public/_repo_clone/src/lilith_replay_core/__init__.py#L1-L10) → `__version__ = "0.2.0"`
- Changelog includes v0.2.0 section: [CHANGELOG.md](file:///c:/workspace_lilith_public/_repo_clone/CHANGELOG.md#L15-L27)
- Releases doc marks v0.2.0 as released: [releases.md](file:///c:/workspace_lilith_public/_repo_clone/docs/releases.md#L1-L30)

## Release Scope (v0.2.0)

This release represents “database-backed replay platform maturity”:

- PostgreSQL integration
- SQLAlchemy data access layer
- Alembic migrations for schema versioning
- Persistence layer (replay runs and artifact records)
- DB-backed lineage retrieval
- Railway deployment configuration and healthcheck behavior
- Prometheus monitoring and a stable metrics surface
- Grafana dashboard assets + live setup documentation
- Portfolio curation and navigation documents

## Delivered Capabilities (Verifiable)

### API

- Swagger UI: `GET /docs`
- OpenAPI schema: `GET /openapi.json`
- Health: `GET /health`
- DB health: `GET /health/db`

### Persistence / Lineage

- Create replay run: `POST /api/v1/replay/run`
- Read replay run: `GET /api/v1/replay/run/{run_id}`
- Read lineage: `GET /api/v1/lineage/{run_id}`

### Observability

- Metrics endpoint: `GET /metrics`
- Metrics documented: [observability.md](file:///c:/workspace_lilith_public/_repo_clone/docs/observability.md)
- Grafana dashboard JSON: [grafana_dashboard_lilith_replay_public.json](file:///c:/workspace_lilith_public/_repo_clone/grafana_dashboard_lilith_replay_public.json)
- Grafana live guide: [grafana_live.md](file:///c:/workspace_lilith_public/_repo_clone/docs/grafana_live.md)

## Deployment Status (Expected)

Railway:

- Deploy config: [railway.json](file:///c:/workspace_lilith_public/_repo_clone/railway.json)
- Deployment guide: [railway_deployment.md](file:///c:/workspace_lilith_public/_repo_clone/docs/railway_deployment.md)
- Healthcheck path: `/health`

Important operational property:

- Container startup is migration-gated (`alembic upgrade head` must succeed before the web server starts).

## Documentation Status

Portfolio navigation / UX docs present:

- Audit report: [PORTFOLIO_HARDENING_AUDIT.md](file:///c:/workspace_lilith_public/_repo_clone/PORTFOLIO_HARDENING_AUDIT.md)
- Repo map: [repository_map.md](file:///c:/workspace_lilith_public/_repo_clone/docs/repository_map.md)
- Operator runbook: [operator_runbook.md](file:///c:/workspace_lilith_public/_repo_clone/docs/operator_runbook.md)
- Releases doc: [releases.md](file:///c:/workspace_lilith_public/_repo_clone/docs/releases.md)
- Screenshot plan: [screenshots.md](file:///c:/workspace_lilith_public/_repo_clone/docs/screenshots.md)

## Release Readiness Conclusion

- Versioning: consistent
- Capabilities: documented and verifiable via public endpoints
- Observability: dashboard asset is included; live Grafana requires external provisioning
- Remaining risk: live deployment base URL is environment-specific and remains a placeholder in docs unless explicitly filled in at release time

