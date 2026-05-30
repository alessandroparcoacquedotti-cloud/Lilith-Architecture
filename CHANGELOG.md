# Changelog

This project follows Semantic Versioning principles as a baseline.

## v0.1.0

Initial public release foundation:

- Public-safe FastAPI service for deterministic manifest validation and artifact diffing
- Structured JSON logging with request correlation (`X-Request-ID`)
- Prometheus metrics and `/metrics` endpoint (configurable via `ENABLE_METRICS`)
- Docker-first deployment flow with Railway and Render configuration
- Public-safe documentation for observability and deployment
