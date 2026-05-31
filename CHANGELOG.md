# Changelog

This project follows Semantic Versioning principles as a baseline.

## v0.1.0

Initial public release foundation:

- Public-safe FastAPI service for deterministic manifest validation and artifact diffing
- Structured JSON logging with request correlation (`X-Request-ID`)
- Prometheus metrics and `/metrics` endpoint (configurable via `ENABLE_METRICS`)
- Docker-first deployment flow with Railway and Render configuration
- Public-safe documentation for observability and deployment

## v0.2.0

Database-backed replay platform milestone:

- PostgreSQL integration for deployed persistence
- SQLAlchemy layer for DB access and transactional workflows
- Alembic migrations for schema versioning and upgrades
- Persistence layer for replay runs and artifact records
- DB-backed lineage retrieval for persisted runs
- Railway deployment hardening and operational health checks
- Prometheus monitoring expanded for API, replay, lineage, and DB operations
- Grafana dashboard assets (JSON export) and live setup documentation
- Portfolio curation (README quick verification, repository map, operator runbook, releases doc)
