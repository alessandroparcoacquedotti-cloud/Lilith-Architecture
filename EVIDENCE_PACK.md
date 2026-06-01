# Evidence Pack (v0.2.0)

Objective: assemble a complete, recruiter-friendly evidence package for Lilith Replay Core (v0.2.0) without changing backend functionality.

## Phase 1 — Live URL Discovery (Result)

Repository audit result:

- The live Railway public URL is **not stored in the repository** (expected; it’s environment-specific).
- Swagger/Health/DB Health/Metrics paths are documented; only the base domain is missing.

### Where to insert the real Railway URL

Replace placeholders with your real base URL (example format: `https://your-service-name.up.railway.app`):

1. README live base URL:
   - [README.md](file:///c:/workspace_lilith_public/_repo_clone/README.md) → `Deployed (Railway): https://<railway-public-domain>`
2. Recruiter quick start live base URL:
   - [recruiter_quick_start.md](file:///c:/workspace_lilith_public/_repo_clone/docs/recruiter_quick_start.md) → `Live (Railway): https://<railway-public-domain>`
3. Operator runbook deployed base URL:
   - [operator_runbook.md](file:///c:/workspace_lilith_public/_repo_clone/docs/operator_runbook.md) → `Deployed: https://<railway-public-domain>`
4. Grafana ingestion guide API domain placeholder:
   - [grafana_live.md](file:///c:/workspace_lilith_public/_repo_clone/docs/grafana_live.md) → replace `<your-api-domain>` / `<your-api-domain-without-scheme>`

### Final live URLs (derived)

Once you have the base URL:

- Swagger: `<BASE_URL>/docs`
- Health: `<BASE_URL>/health`
- DB Health: `<BASE_URL>/health/db`
- Metrics: `<BASE_URL>/metrics`

## Phase 2 — Screenshot Preparation

These screenshots are the “portfolio proof” set. Capture them after confirming the live base URL.

### 1) GitHub repository homepage

Why it matters:

- establishes credibility in 15 seconds (what/why/how to verify)

Demonstrates:

- communication, documentation discipline, OSS hygiene

Where to use:

- README (top)
- LinkedIn carousel (slide 1)

### 2) GitHub release v0.2.0

Why it matters:

- shows release discipline and versioned milestones

Demonstrates:

- shipping mindset, semantic versioning, changelog hygiene

Where to use:

- README Evidence section
- LinkedIn carousel (near the end, “shipped v0.2.0”)

### 3) Swagger UI (`/docs`)

Why it matters:

- makes the API explorable without reading code

Demonstrates:

- API design + documentation, contract-first verification

Where to use:

- README Evidence
- LinkedIn carousel

### 4) Health endpoint (`/health`)

Why it matters:

- verifies deploy readiness and operational posture

Demonstrates:

- platform thinking (health checks, stable responses, request IDs)

Where to use:

- README Evidence
- LinkedIn carousel

### 5) DB health endpoint (`/health/db`)

Why it matters:

- proves DB wiring/migration posture without leaking secrets

Demonstrates:

- production-grade safety design and ops readiness

Where to use:

- README Evidence
- LinkedIn carousel

### 6) Replay creation endpoint (`POST /api/v1/replay/run`)

Why it matters:

- demonstrates persistence and measurable side-effects

Demonstrates:

- backend workflows (transactions, persistence layer, metrics increments)

Where to use:

- README Evidence (gif/screenshot sequence)
- LinkedIn carousel

### 7) Lineage endpoint (`GET /api/v1/lineage/<run_id>`)

Why it matters:

- proves “auditability” and replay lineage as a first-class feature

Demonstrates:

- traceability and DB-backed retrieval

Where to use:

- README Evidence
- LinkedIn carousel

### 8) Grafana dashboard

Why it matters:

- shows operational maturity and live observability

Demonstrates:

- metrics-to-dashboard workflow (platform engineering core skill)

Where to use:

- README Evidence
- LinkedIn carousel

### 9) Railway deployment page

Why it matters:

- confirms real deployment and runtime status

Demonstrates:

- deployment competence and healthcheck awareness

Where to use:

- README Evidence (optional)
- LinkedIn carousel (final “it’s deployed” proof)

## Phase 4 — GitHub Showcase Audit (Quick)

What a recruiter sees in 15 seconds:

- a credible backend project with verification endpoints, tests/typing/lint, and observability artifacts

What a platform engineer sees:

- health endpoints + Prometheus metrics + a Grafana dashboard export + migration-gated startup documented

What still causes confusion:

- the live Railway base URL is not one-click (placeholders must be filled at release time)

Recommendations:

- after adding the real base URL, re-order the README “Live Verification” links to include exact live URLs (not just paths)
- add 1–2 screenshots into README Evidence section (Swagger + Grafana) for instant proof

