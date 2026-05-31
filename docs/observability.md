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
- `db_transactions_total{operation, result}`
- `db_operation_duration_seconds{operation}`
- `replay_validation_requests_total{status}`
- `validation_failures_total`
- `deterministic_diff_requests_total{format, status}`
- `schema_drift_detected_total{format}`
- `replay_runs_created_total{replay_type, status}`
- `artifact_records_created_total{artifact_type}`
- `lineage_requests_total{status}`

Cardinality policy:

- `path` uses the FastAPI route template, not raw request paths.
- Do not add labels that can contain user-provided identifiers.

## Metrics Catalog

### API

- `api_requests_total{method, path, status}`
- `api_request_duration_seconds{method, path, status}`
- `api_startups_total`

### Replay / Artifacts / Lineage

- `replay_runs_created_total{replay_type, status}`
  - `status`: `created` (current scope)
- `artifact_records_created_total{artifact_type}`
- `lineage_requests_total{status}`
  - `status`: `success | not_found | error`

### Database

- `db_connectivity_checks_total{result}`
  - `result`: `pass | fail` (connectivity-only, used by `/health/db`)
- `db_transactions_total{operation, result}`
  - `operation`: `create_replay | read_replay | read_lineage`
  - `result`: `success | failure`
- `db_operation_duration_seconds{operation}`
  - histogram of DB operation latency

## Example Prometheus Queries

- Replay run throughput by type:
  - `sum by (replay_type) (rate(replay_runs_created_total[5m]))`
- Artifact write throughput by type:
  - `sum by (artifact_type) (rate(artifact_records_created_total[5m]))`
- Lineage 404 rate:
  - `rate(lineage_requests_total{status="not_found"}[5m])`
- DB failure rate by operation:
  - `sum by (operation) (rate(db_transactions_total{result="failure"}[5m]))`
- P95 DB latency by operation:
  - `histogram_quantile(0.95, sum by (le, operation) (rate(db_operation_duration_seconds_bucket[5m])))`

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
