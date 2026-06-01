# Screenshot Priority Matrix (v0.2.0)

Objective: define the smallest possible screenshot set that still preserves a portfolio-grade **A** evaluation for backend + platform engineering signals.

Sources audited:

- [README.md](file:///c:/workspace_lilith_public/_repo_clone/README.md)
- [screenshots.md](file:///c:/workspace_lilith_public/_repo_clone/docs/screenshots.md)
- [EVIDENCE_PACK.md](file:///c:/workspace_lilith_public/_repo_clone/EVIDENCE_PACK.md)
- [LINKEDIN_POST_V2_PREP.md](file:///c:/workspace_lilith_public/_repo_clone/LINKEDIN_POST_V2_PREP.md)

## Minimum “Grade A” Screenshot Package (Smallest Set)

**Minimum set: 5 screenshots**

1) GitHub repository homepage  
2) Swagger UI (`/docs`)  
3) Replay run creation (`POST /api/v1/replay/run`)  
4) Grafana dashboard overview (rates + API p95 + DB p95 panels)  
5) Railway deployment page (service healthy)  

Rationale:

- Covers “shipped repo + live API + DB-backed workflow + observability + real deployment” without redundancy.
- DB health and lineage are valuable, but can be inferred if replay creation + Grafana DB panels are clearly visible; include them when possible (see NICE_TO_HAVE).

## Priority Matrix

### MUST_HAVE

#### 1) GitHub repository homepage

- Engineering signal shown: repo clarity, CI badge, verification-first documentation, OSS readiness.
- Recruiter value: fastest credibility and context (what/why/how to verify) in one frame.
- LinkedIn value: strongest “cover slide” for a carousel; establishes legitimacy.
- README value: supports the “Evidence” section by proving the repo is curated and navigable.

#### 2) Swagger UI (`/docs`)

- Engineering signal shown: contract-first API surface, public discoverability, clean schema.
- Recruiter value: “I can explore the API now” without code review.
- LinkedIn value: visually conveys “real backend” and verifiable endpoints.
- README value: anchors Live Verification; shows the API is not hypothetical.

#### 3) Replay run creation (`POST /api/v1/replay/run`)

- Engineering signal shown: persistence workflow (write path), DB-backed system behavior, measurable side-effects.
- Recruiter value: distinguishes project from “hello world API” (it performs real work).
- LinkedIn value: high-signal “action → response” screenshot, easy to understand.
- README value: pairs with walkthrough/evidence to show end-to-end capability.

#### 4) Grafana dashboard (overview)

- Engineering signal shown: operational maturity (metrics-to-dashboard), SLO-adjacent thinking (rates/latency), DB observability.
- Recruiter value: rare signal; indicates you can operate systems, not just implement endpoints.
- LinkedIn value: strongest “platform engineering” visual proof.
- README value: substantiates the “Monitoring” claim and Grafana assets in-repo.

#### 5) Railway deployment page (service healthy)

- Engineering signal shown: deployability, runtime health, platform workflow literacy.
- Recruiter value: converts “deployed” from a claim into proof.
- LinkedIn value: closes the story (“it runs in production”).
- README value: supports Evidence section and makes Live Verification credible.

### NICE_TO_HAVE

#### 6) DB health endpoint (`/health/db`)

- Engineering signal shown: DB connectivity verification + migration posture exposed safely (non-leaky).
- Recruiter value: strong “production-minded” signal without needing deep technical context.
- LinkedIn value: adds credibility to “Postgres + migrations” claims.
- README value: reinforces the Live Verification section and ops posture.

#### 7) Lineage lookup (`GET /api/v1/lineage/<run_id>`)

- Engineering signal shown: auditability/traceability; read-path correctness for persisted data.
- Recruiter value: connects the project narrative (“replay/audit platform”) to a concrete API capability.
- LinkedIn value: shows “write then read back lineage” storyline.
- README value: complements replay creation as the proof of “DB-backed lineage.”

#### 8) GitHub Release `v0.2.0`

- Engineering signal shown: release discipline, semantic versioning, changelog hygiene.
- Recruiter value: signals “shipping” and iteration, not just a repo dump.
- LinkedIn value: reinforces timeline and progress since v0.1.0.
- README value: optional; better as a link than a screenshot if you’re minimizing assets.

### OPTIONAL

#### 9) Health endpoint (`/health`)

- Engineering signal shown: basic operational readiness, process-level health.
- Recruiter value: low-to-medium (often redundant if Railway healthy + Swagger works).
- LinkedIn value: low (less visually interesting).
- README value: useful for text verification, not essential as a screenshot if space is limited.

## Ranked List (Most → Least Important)

1) GitHub repository homepage  
2) Grafana dashboard overview  
3) Swagger UI (`/docs`)  
4) Replay run creation (`POST /api/v1/replay/run`)  
5) Railway deployment page (healthy)  
6) DB health (`/health/db`)  
7) Lineage lookup (`/api/v1/lineage/<run_id>`)  
8) GitHub Release `v0.2.0`  
9) Health (`/health`)  

## Notes on Avoiding Redundancy

- If you include Railway “healthy” + Swagger, a separate `/health` screenshot adds little.
- If Grafana panels clearly show DB latency and replay/lineage activity increasing, `/health/db` becomes less critical (but still a very strong NICE_TO_HAVE).
- If you capture both replay creation and lineage lookup, you can skip the GitHub Release screenshot without losing technical signal.

