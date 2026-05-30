# Observability (Public-Safe)

This repository exposes a public-safe replay validation and deterministic diff platform. Observability is designed to be:

- Structured and machine-parsable (JSON logs).
- Deterministic in shape and formatting (stable field names, stable timestamp formatting).
- Public-safe (no prediction logic, no betting logic, no private datasets, no operational thresholds, no secrets).

## Metrics Overview

The API exposes Prometheus metrics at:

- `GET /metrics`

Key metrics:

- `api_requests_total{method, path, status}`
- `api_request_duration_seconds{method, path, status}`
- `api_startups_total`
- `db_connectivity_checks_total{result}`
- `replay_validation_requests_total{status}`
- `validation_failures_total`
- `deterministic_diff_requests_total{format, status}`
- `schema_drift_detected_total{format}`

Cardinality policy:

- `path` uses the FastAPI route template, not raw request paths.
- Do not add labels that can contain user-provided identifiers.

## Logging Philosophy

Logs are emitted as one JSON object per line to stdout, suitable for container logging pipelines.

Core fields:

- `ts`, `level`, `logger`, `message`
- `request_id` (propagated via `X-Request-ID`)
- `replay_run_id` (when applicable)
- `event` (stable event name)

Public safety rules:

- Never log request bodies or artifacts.
- Never log credentials or connection strings.
