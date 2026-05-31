# Lilith Replay Core

[![CI](https://github.com/alessandroparcoacquedotti-cloud/Lilith-Architecture/actions/workflows/ci.yml/badge.svg)](https://github.com/alessandroparcoacquedotti-cloud/Lilith-Architecture/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)

Public-safe FastAPI backend that exposes deterministic validation + artifact diff primitives for replay/audit workflows.

## Table of Contents

- [Overview](#overview)
- [Live Verification](#live-verification)
- [Quick Verification Walkthrough (2–3 minutes)](#quick-verification-walkthrough-23-minutes)
- [Architecture](#architecture)
- [Public Replay Platform](#public-replay-platform)
- [API](#api)
- [Monitoring](#monitoring)
- [Development](#development)
- [Repository Structure](#repository-structure)
- [Roadmap](#roadmap)

## Overview

This project exists to demonstrate portfolio-grade backend engineering around a “public-safe replay platform” concept:

- deterministic request validation (replay manifests)
- deterministic artifact diffing (CSV/JSON) with stable hashing and stable summaries
- structured JSON logging with request correlation (`X-Request-ID`) and replay correlation (`replay_run_id`)
- Prometheus metrics (`/metrics`) with low-cardinality labels
- optional Postgres connectivity checks (`/health/db`) for deployment verification

This repository intentionally does not contain: prediction logic, betting logic, private datasets, operational thresholds, or secrets.

## Live Verification

Base URL:

- Local (Docker / uvicorn): `http://localhost:8000`
- Deployed (Railway/Render): `https://<your-public-service-domain>`

Endpoints (exact paths):

- Swagger UI: `GET /docs`
- Health: `GET /health`
- Database health: `GET /health/db`
- Metrics: `GET /metrics`

Exact URLs (local example):

- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- DB health: `http://localhost:8000/health/db`
- Metrics: `http://localhost:8000/metrics`

## Quick Verification Walkthrough (2–3 minutes)

Step 1: Open Swagger

- Open: `http://localhost:8000/docs`
- Expected: Swagger UI loads and shows `Lilith Replay Platform (Public)`

Step 2: Call “replay validation” (manifest validation)

- Endpoint: `POST /api/v1/manifests/validate`
- Payload:

```json
{
  "run_id": "run-123",
  "replay_timestamp": "2026-01-01T00:00:00Z",
  "fixtures_processed": 1,
  "audit_schema_version": "v1",
  "integrity_hash": "abc"
}
```

- Expected: HTTP 200 with `{"ok": true, "errors": [], ...}`

Step 3: Retrieve lineage

- Endpoint: `GET /api/v1/lineage/{run_id}`
- Call: `GET /api/v1/lineage/run-123`
- Expected: HTTP 200 with `{"ok": true, "record": {"run_id": "run-123", ...}}`

Step 4: Verify metrics

- Open: `http://localhost:8000/metrics`
- Expected: Prometheus exposition text including these metric names:
  - `api_requests_total`
  - `api_request_duration_seconds`
  - `replay_validation_requests_total`
  - `deterministic_diff_requests_total`

## Architecture

Architecture material is intentionally kept in-repo (public-safe):

- [development.md](docs/development.md)
- [deployment.md](docs/deployment.md)
- [observability.md](docs/observability.md)
- [philosophy.md](docs/philosophy.md)
- [operator_runbook.md](docs/operator_runbook.md)
- [releases.md](docs/releases.md)
- [repository_map.md](docs/repository_map.md)

## Public Replay Platform

This codebase is “replay platform scaffolding”: it focuses on the deterministic and auditable primitives that sit around a replay engine.

What you can verify end-to-end via the public API:

- request validation (schema + fail-closed behavior) for replay manifests
- deterministic diffing for JSON/CSV artifacts
- request correlation + stable telemetry signals for monitoring

## API

Core endpoints:

- `GET /health`
- `GET /health/db`
- `GET /docs`
- `GET /openapi.json`
- `GET /metrics` (when `ENABLE_METRICS=1`)

Versioned API:

- `POST /api/v1/manifests/validate`
- `POST /api/v1/diff/json`
- `POST /api/v1/diff/csv`
- `GET /api/v1/lineage/{run_id}`

## Monitoring

Prometheus:

- Scrape endpoint: `GET /metrics`
- Docs: [observability.md](docs/observability.md)

## Development

Local setup + checks:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev,db,api]"
ruff check src tests scripts_public
mypy src
pytest
```

Local API:

```bash
uvicorn lilith_replay_core.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Docker (recommended for a one-command run):

```bash
docker build -t lilith-replay .
docker run --rm -p 8000:8000 -e APP_ENV=production -e LOG_LEVEL=INFO lilith-replay
```

Docker Compose (API + Postgres):

```bash
docker compose up --build
```

Deployment notes:

- Railway: [railway.json](railway.json)
- Render: [render.yaml](render.yaml)
- Docs: [deployment.md](docs/deployment.md)

## Repository Structure

- `docs/`: design notes, public-safe architecture, and operational docs (see [repository_map.md](docs/repository_map.md))
- `src/`: Python package (`lilith_replay_core`)
- `tests/`: pytest suite
- `scripts_public/`: small, public-safe helper scripts
- `examples/`: sample public-safe payloads/artifacts

## Roadmap

- [roadmap.md](docs/roadmap.md)
