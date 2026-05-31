# Grafana Live (Public Metrics)

Objective: run a fully operational Grafana instance connected to the live Prometheus metrics for Lilith Replay Platform, then import the published dashboard JSON and verify panels render live data.

## 1) Simplest Free Deployment Path

Preferred order:

### A) Grafana Cloud Free (recommended)

Why:

- Hosted Grafana (no server maintenance, TLS, user management, or upgrades).
- Designed for Prometheus metrics workflows.
- Fastest path to a “shareable portfolio dashboard” once ingestion is configured.

Trade-off:

- You still need a small “scraper/agent” that can fetch your `/metrics` and send them to Grafana Cloud Metrics (Prometheus remote_write).

### B) Railway Grafana

Why not first:

- Grafana alone is not enough; you still need Prometheus (or Mimir) to store metrics.
- Running Prometheus + Grafana on free tiers is typically constrained by disk/retention and can be reset by restarts.

When to choose it:

- You want everything self-hosted for demo purposes and accept short retention.

### C) Alternative free solutions

Examples:

- Render/Fly.io for Grafana + Prometheus (same constraints as Railway).
- A local-only Grafana + Prometheus compose (great for demos, not “live hosted”).

## 2) Metrics Requirements

The datasource must expose these metric families (the dashboard queries rely on them):

- `api_requests_total`
- `api_request_duration_seconds` (histogram)
- `replay_runs_created_total`
- `artifact_records_created_total`
- `lineage_requests_total`
- `db_transactions_total`
- `db_operation_duration_seconds` (histogram)

Quick existence checks in PromQL:

- `api_requests_total`
- `api_request_duration_seconds_bucket`
- `replay_runs_created_total`
- `artifact_records_created_total`
- `lineage_requests_total`
- `db_transactions_total`
- `db_operation_duration_seconds_bucket`

## 3) Grafana Cloud Free: Working Setup

### Step 1: Create Grafana Cloud stack

1. Create a Grafana Cloud account.
2. Create a new Stack (Free tier).
3. Open the Stack’s Grafana URL (hosted Grafana UI).

### Step 2: Create a Metrics (Prometheus) ingestion token

In Grafana Cloud:

1. Go to “Connections” → “Grafana Cloud Metrics” (Prometheus).
2. Create an access policy token that has permission to write metrics.
3. Copy the values Grafana provides for remote_write (endpoint URL, username/instance ID, and API token/password).

### Step 3: Deploy Grafana Alloy to scrape `/metrics` and remote_write to Cloud

Grafana Cloud does not scrape your app directly. You deploy a small agent that:

- scrapes your API metrics endpoint (`https://<your-api-domain>/metrics`)
- forwards those samples to Grafana Cloud via Prometheus remote_write

Recommended: run Grafana Alloy as a small container service on the same platform as the API (Railway is fine for this).

Alloy config (minimal Prometheus scrape + remote_write):

```hcl
prometheus.scrape "lilith_api" {
  targets = [
    { "__address__" = "<your-api-domain-without-scheme>", "job" = "lilith-api" },
  ]
  metrics_path = "/metrics"
  scheme       = "https"
  scrape_interval = "15s"
  forward_to = [prometheus.remote_write.grafana_cloud.receiver]
}

prometheus.remote_write "grafana_cloud" {
  endpoint {
    url = "<GRAFANA_CLOUD_PROM_REMOTE_WRITE_URL>"
    basic_auth {
      username = "<GRAFANA_CLOUD_USERNAME>"
      password = "<GRAFANA_CLOUD_API_TOKEN>"
    }
  }
}
```

Operational notes:

- Keep `scrape_interval` at 15s–30s.
- Ensure your `/metrics` endpoint is publicly reachable from the agent.
- If your API is HTTP (not HTTPS) behind internal routing, set `scheme = "http"` accordingly.

### Step 4: Datasource configuration in Grafana

In Grafana Cloud stacks, a Prometheus datasource is usually provisioned automatically (“Grafana Cloud Prometheus”).

Validate datasource:

1. Grafana → “Connections” → “Data sources” → Prometheus.
2. Open “Explore”.
3. Run: `api_requests_total`

Success criteria:

- Query returns a non-empty series.
- Labels are present (e.g., `method`, `path`, `status`) for `api_requests_total`.

## 4) Import the Dashboard JSON

Dashboard file:

- [grafana_dashboard_lilith_replay_public.json](../grafana_dashboard_lilith_replay_public.json)

Import steps:

1. Grafana → “Dashboards” → “New” → “Import”.
2. Upload/paste the JSON from `grafana_dashboard_lilith_replay_public.json`.
3. When prompted for the datasource variable `DS_PROMETHEUS`, select your Prometheus datasource (Grafana Cloud Prometheus).
4. Save the dashboard.

## 5) Verify Every Panel Renders Data

Dashboard panels and required metrics:

- Replay Runs Created (rate) → `replay_runs_created_total`
- Artifact Records Created (rate) → `artifact_records_created_total`
- Lineage Requests (rate) → `lineage_requests_total`
- DB Transactions (rate) → `db_transactions_total`
- API Request Rate (by path/status) → `api_requests_total`
- API Request Duration (p95 by path) → `api_request_duration_seconds_bucket`
- DB Operation Duration (p95 by operation) → `db_operation_duration_seconds_bucket`

If a panel is blank:

- First verify the raw metric exists in Explore.
- Then verify you are looking at a wide enough time range (last 6h is default).
- Then generate traffic (next section).

## 6) Live Validation (Metrics Move)

Goal: generate events that increment the same counters shown in the dashboard.

### Step 1: Create replay run

Call the replay endpoint to create a run:

- `POST /api/v1/replay/run`

Example payload:

```json
{
  "replay_type": "demo",
  "manifest_hash": "manifest-abc",
  "artifacts": [
    { "artifact_type": "json", "artifact_hash": "artifact-1" },
    { "artifact_type": "csv", "artifact_hash": "artifact-2" }
  ]
}
```

Expected:

- `replay_runs_created_total` increases
- `artifact_records_created_total` increases (if artifacts are persisted per run)
- `db_transactions_total` increases (if DB is used)
- `db_operation_duration_seconds` histogram gets samples

### Step 2: Create lineage request

Call:

- `GET /api/v1/lineage/<run_id>`

Expected:

- `lineage_requests_total` increases
- `api_requests_total` increases for the lineage path
- latency panels show new samples

### Step 3: Refresh dashboard

1. Open the dashboard.
2. Click “Refresh” (or wait for auto refresh, default 30s).
3. Confirm graphs change (rates/latency lines move).

## 7) Screenshots Checklist (Portfolio)

Required screenshots to capture (manually from the Grafana UI):

- Overview dashboard (full screen)
- Replay metrics panel (“Replay Runs Created (rate)”)
- API latency panel (“API Request Duration (p95 by path)”)
- DB latency panel (“DB Operation Duration (p95 by operation)”)

Tips:

- Set time range to “Last 15 minutes” right after live validation so changes are obvious.
- Keep refresh at 30s and capture after a manual refresh.

## 8) Result Flags

These are the target acceptance criteria for “Grafana live” completion:

- `GRAFANA_LIVE = YES` when a hosted Grafana instance is reachable publicly.
- `DATASOURCE_CONNECTED = YES` when Explore queries return the required metric families.
- `PANELS_RENDERING = YES` when all dashboard panels show non-empty data.
- `LIVE_VALIDATION_PASSED = YES` when generating replay + lineage traffic visibly moves panels.
- `SCREENSHOTS_READY = YES` when the four screenshots above are captured and stored for the portfolio.
