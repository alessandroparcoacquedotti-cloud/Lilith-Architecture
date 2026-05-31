# Portfolio Screenshots Guide

Goal: capture a small set of screenshots that communicate “this is real, deployed, observable, and verifiable” in under 60 seconds for recruiters and hiring managers.

Recommended naming convention:

- `screenshots/01_github_home.png`
- `screenshots/02_railway_deploy_success.png`
- `screenshots/03_swagger_docs.png`
- `screenshots/04_health_ok.png`
- `screenshots/05_health_db.png`
- `screenshots/06_grafana_overview.png`
- `screenshots/07_replay_run_created.png`
- `screenshots/08_lineage_lookup.png`

Do not commit screenshots that contain:

- secrets (tokens, passwords, connection strings)
- private data
- personally identifying information

## 1) GitHub repository homepage

What it shows:

- project title, one-line purpose, CI badge, and “Live Verification” paths

Skill it demonstrates:

- engineering communication and repo usability

Why recruiters care:

- reduces ambiguity; shows you can present work clearly and quickly

## 2) Railway deployment success

What it shows:

- service is deployed, running, and healthy in a real platform environment

Skill it demonstrates:

- deployment fluency and platform awareness (build/deploy/runtime health)

Why recruiters care:

- converts “I can deploy” from a claim into evidence

## 3) Swagger UI (`/docs`)

What it shows:

- API schema is public, explorable, and stable

Skill it demonstrates:

- contract-first mindset (OpenAPI), operational transparency, and API quality

Why recruiters care:

- enables fast evaluation without reading code

## 4) Health endpoint (`/health`)

What it shows:

- the service responds with HTTP 200 and a small public-safe payload

Skill it demonstrates:

- operational readiness (health checks, structured status)

Why recruiters care:

- confirms the service is alive and predictable

## 5) DB Health endpoint (`/health/db`)

What it shows:

- database connectivity/migration posture is exposed in a safe, non-leaky way

Skill it demonstrates:

- production-minded health design (DB verification without leaking secrets)

Why recruiters care:

- indicates real backend experience beyond “toy API”

## 6) Grafana dashboard (overview)

What it shows:

- live monitoring UI with API rate/latency and DB panels

Skill it demonstrates:

- observability and platform engineering fundamentals (metrics → dashboard)

Why recruiters care:

- demonstrates you can operate and verify systems, not just code them

## 7) Replay run creation (`POST /api/v1/replay/run`)

What it shows:

- a request that triggers persistence and increments replay/artifact metrics

Skill it demonstrates:

- backend workflow design: persistence, transactions, and measurable side-effects

Why recruiters care:

- shows a “system does work” action, not just static endpoints

## 8) Lineage lookup (`GET /api/v1/lineage/<run_id>`)

What it shows:

- reading back DB-backed lineage for a run (or not-found behavior)

Skill it demonstrates:

- auditability: traceability/lineage as a first-class API concern

Why recruiters care:

- ties the project’s narrative (“replay/audit platform”) to a concrete verifiable capability

