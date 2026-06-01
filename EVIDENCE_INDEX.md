# Evidence Index (Screenshots)

This index defines the portfolio screenshot set and where each image should be embedded.

Storage location:

- `docs/images/evidence/`

Naming goal:

- stable filenames so README/LinkedIn references don’t break

## Screenshot Inventory

Status meanings:

- `FOUND`: image exists in `docs/images/evidence/`
- `MISSING`: image not yet added to the repo

| Evidence | Filename (expected) | Status | Caption (recommended) | Where to use |
|---|---|---:|---|---|
| Repository Screenshot | `docs/images/evidence/01_github_home.png` | MISSING | “Repository landing: Live Verification + Evidence links.” | README Evidence, LinkedIn slide 1 |
| Release Screenshot | `docs/images/evidence/02_github_release_v0_2_0.png` | MISSING | “GitHub Release v0.2.0: shipped milestones (persistence, lineage, monitoring).” | README Evidence, LinkedIn mid/late |
| Railway Deployment Screenshot | `docs/images/evidence/03_railway_deploy_healthy.png` | MISSING | “Railway deployment: service running and healthy.” | README Evidence (optional), LinkedIn final |
| Swagger Screenshot | `docs/images/evidence/04_swagger_docs.png` | MISSING | “Swagger UI (/docs): public API contract + interactive verification.” | README Evidence, LinkedIn |
| Health Screenshot | `docs/images/evidence/05_health_ok.png` | MISSING | “/health: process-level health + request ID header.” | README Evidence (optional), LinkedIn |
| DB Health Screenshot | `docs/images/evidence/06_health_db.png` | MISSING | “/health/db: DB connectivity + migration posture (safe, non-leaky).” | README Evidence, LinkedIn |
| Metrics Screenshot | `docs/images/evidence/07_metrics.png` | MISSING | “/metrics: Prometheus exposition with API/replay/lineage/DB metrics.” | README Evidence (optional), LinkedIn |
| Grafana Dashboard Screenshot | `docs/images/evidence/08_grafana_dashboard.png` | MISSING | “Grafana dashboard: API rate/latency + DB p95 panels rendering live data.” | README Evidence, LinkedIn |

## How to Add Screenshots (Manual Step)

1. Capture screenshots from the live services:
   - GitHub repo homepage
   - GitHub Release v0.2.0
   - Railway deployment page (healthy)
   - Swagger UI (`/docs`)
   - `/health`
   - `/health/db`
   - `/metrics`
   - Grafana dashboard
2. Save them using the filenames listed above.
3. Place them under `docs/images/evidence/`.

## Optional: README Embed Snippets

After the images are added, embed them in README using:

```md
![Repository landing](docs/images/evidence/01_github_home.png)
```

