# Recruiter Quick Start (60 seconds)

## What this is

Lilith Replay Platform (Public) is a portfolio-grade backend service that demonstrates how to build and operate a **public-safe replay/audit backend**: validate replay inputs, persist replay runs + artifacts, expose lineage, and provide first-class observability.

## Why it exists

Replay/audit systems exist to answer: “what did we know at the time, what did we produce, and can we prove it deterministically?”

This repo demonstrates that engineering surface area without exposing private datasets, secrets, or internal decision logic.

## What’s deployed

- FastAPI service (Swagger/OpenAPI)
- PostgreSQL-backed persistence (runs + artifact records)
- Alembic migrations
- Prometheus metrics endpoint
- Grafana dashboard JSON export (importable into Grafana)

## How to verify it works (click-first)

Base URL:

- Live (Railway): `https://<railway-public-domain>`
- Local: `http://localhost:8000`

Verify:

- Swagger UI: `/docs`
- Health: `/health`
- DB Health: `/health/db`
- Metrics: `/metrics`

## Stack

- Python 3.11+
- FastAPI + Uvicorn
- PostgreSQL
- SQLAlchemy
- Alembic
- Prometheus metrics
- Grafana dashboard assets
- Ruff + Mypy + Pytest + CI
- Docker + Docker Compose
- Railway deployment config

## Skills this demonstrates

- backend fundamentals: API design, validation, persistence, migrations
- platform fundamentals: health checks, metrics, dashboards, deployability
- engineering hygiene: typed Python, linting, tests, CI, Docker
- security posture: public-safe boundaries and “no secrets in repo” discipline

