# LinkedIn Post Prep (v0.2.0) — Do Not Post Yet

Objective: prepare a high-signal LinkedIn post plan with evidence attachments. This file is a checklist and outline only.

## Accomplishments Since v0.1.0

- Shipped v0.2.0 with PostgreSQL-backed persistence and DB-backed lineage.
- Added Alembic migrations and an explicit migration posture for deployment.
- Expanded Prometheus metrics surface for API/replay/lineage/DB operations.
- Published a Grafana dashboard JSON export and a live Grafana setup guide.
- Hardened repo presentation for recruiter/platform evaluation (runbooks, repo map, topology, screenshot plan).

## Major Engineering Milestones (Talking Points)

- **Backend:** request validation + deterministic diff primitives exposed as a public-safe API.
- **Data:** SQLAlchemy persistence layer storing replay runs and artifact records.
- **Migrations:** Alembic-managed schema with migration-gated startup in deployment.
- **Operational readiness:** `/health`, `/health/db`, `/metrics`, and a Grafana dashboard for rates/latency.
- **Engineering hygiene:** tests, typing, linting, CI, Docker, and reproducible local/dev workflows.
- **Public-safe boundaries:** no secrets, no private datasets, no internal decision logic.

## Screenshots to Attach (Recommended Order)

1. GitHub repo homepage (Live Verification + Evidence visible)
2. GitHub Release `v0.2.0`
3. Swagger UI (`/docs`)
4. Health (`/health`)
5. DB Health (`/health/db`)
6. Replay creation request + response (`POST /api/v1/replay/run`)
7. Lineage lookup (`GET /api/v1/lineage/<run_id>`)
8. Grafana dashboard overview (rates + API p95 + DB p95 panels)
9. Railway deployment page (service healthy)

Reference the capture checklist:

- [screenshots.md](file:///c:/workspace_lilith_public/_repo_clone/docs/screenshots.md)

## Key Links to Include (fill in before posting)

- GitHub repo: `https://github.com/<owner>/<repo>`
- GitHub Release v0.2.0: `https://github.com/<owner>/<repo>/releases/tag/v0.2.0`
- Live API base URL (Railway): `https://<railway-public-domain>`
- Swagger: `https://<railway-public-domain>/docs`
- Metrics: `https://<railway-public-domain>/metrics`
- Grafana dashboard (if public): `<grafana-public-url>`

## Key Claims (Keep These Concrete)

- “Deployed backend with public health + metrics endpoints”
- “DB-backed persistence + lineage”
- “Prometheus metrics and Grafana dashboard panels rendering live data”
- “Typed Python + linting + tests + CI + Docker”

## Risk / Safety Notes

- Ensure screenshots contain no secrets (tokens, connection strings, Railway variables).
- If Grafana is not public, show screenshots only (no public link).
- Do not claim “Grafana live” unless the dashboard panels are visibly rendering non-empty data.

