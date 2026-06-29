# PROJECT_STATE — DrivePulse Lakehouse
_Last updated: 2026-06-29 · session 8 · by Claude_

> Read this first every session. Update it last every session.

## Current phase
**Phase 2 — Claims Silver (built, awaiting review).** Bronze merged to master. Silver built as a
Lakeflow Declarative Pipeline (ADR 0003) on branch `feat/claims-silver`, catalog `prod_claims`.
All EPIC-2 stories done + tested (claim/quarantine/status_history/severity + SCD2 dims). PR open.
Next gate: user review → merge → Gold. (`silver.complaint` deferred with the complaints file.)

## Environment audit (2026-06-25, s3) — VERIFIED
- Tooling: git, gh, az, databricks (CLI 1.5.0), python 3.11 all installed on this machine.
- Auth: Azure ✅ (balantrapu.ravichandra@gmail.com · "Azure subscription 1" 93a8c829… ·
  tenant 2bb692f9…). GitHub ✅ (bravichandra45, keyring; scopes repo/workflow/read:org/gist).
  Databricks ✅ profile `drivepulse` in ~/.databrickscfg using `auth_type = azure-cli`
  (no PAT — reuses the az login token). User is a workspace ADMIN (allow-cluster-create).
- Bundle: `databricks bundle validate` PASSES against dev/real workspace. databricks.yml dev
  host set to real URL; prod host still REPLACE_ME (no separate prod workspace yet).
- Auth note: browser/device login flows are flaky in this setup; azure-cli passthrough is the
  reliable path for Databricks. DATABRICKS_CONFIG_PROFILE=drivepulse is set in .claude/settings.json.
- Databricks workspace EXISTS: `databricks_mission_2026_dataai` · rg_mission_2026_dataai ·
  eastus · premium · URL `adb-7405605467002690.10.azuredatabricks.net`.
- RG is SHARED with a "finance mission" + a SQL app (app-mission-sql/app_mission_db, eastasia).
  Rule: touch only DrivePulse resources; prefix anything new `drivepulse_*`.
- Storage: `adls4missiondataai` (eastus) likely our lake; `adlsfinancemission2026` is finance's.
- Access connectors: `adls_connect_databricks` (ours), `adls_connect_databricks_finanace` (finance's).
- Event Hubs: NOT provisioned yet → needed for telematics streaming.
- Federation candidate: `app-mission-sql` (Azure SQL, eastasia) could host vPIC reference.
- Shell note: Claude's CLI commands run sandboxed w/o network by default; network calls
  (az/databricks/gh that hit cloud) need sandbox disabled per-call.

## Operating model (locked)
- Claude drives; user reviews. One feature at a time with explicit approval gates
  (discuss → direct → develop → approve → close → next).
- **Spine = Claude Code** (decisions write into repo files; build runs against Databricks).
  **Companion = this Claude.ai project** for mobile review + architecture diagrams.
- Continuity = CLAUDE.md (architecture truth) + PROJECT_STATE.md (where we are), kept current.
- Sequence: set up Claude Code project → design architecture (10 topics) → agile plan → build.

## Decisions locked
- Project: DrivePulse Lakehouse — UBI auto-insurance data **mesh**.
- 3 UC catalogs: `prod_telematics` (IoT), `prod_policy` (Underwriting), `prod_claims` (Claims Ops).
- Cloud: Azure · `rg_mission_2026_dataai` · East US · ADLS Gen2 + Databricks + Event Hubs.
- Tooling: Databricks CLI + Declarative Automation Bundles · GitHub Actions CI/CD · public repo.
- Patterns required: Auto Loader · Event Hubs streaming · Lakehouse Federation · Lakeflow
  Declarative Pipelines · SCD2 · CDC · UC governance · Vector Search + RAG · Mosaic AI + MLflow eval.
- Gold = Kimball stars per domain + cross-domain marts. Datasets: VED/eVED, Porto Seguro,
  Allstate, NHTSA (vPIC/FARS/recalls), NOAA/OSM (federated), NHTSA/DOI docs (RAG); real data,
  synthetically linked (documented).
- Isolation: directory scoping is the real lock (project `.claude/` here; job-search skills kept
  in their own repo, out of `~/.claude/skills/`). `strictPluginOnlyCustomization` is
  managed-settings-only — not used for this solo setup.
- **Claims domain LOCKED (ADR 0002):** "Claims Intelligence & Fraud". 5 real sources →
  bronze→silver→gold→ML→GenAI. Facts: fact_claim, fact_claim_lifecycle, fact_claim_status_history,
  fact_complaint. Lifecycle dates derived/synthetic (seeded). Build Bronze-first, PR-gated per phase.
- **Raw landing in ADLS** (not UC-managed volumes): `raw` container of `adls4missiondataai`,
  external Volume `dev_claims.bronze.landing` → `.../claims/landing/`; upload via Databricks identity.
- **GitHub repo: PUBLIC** (`drivepulse-lakehouse`). Data files gitignored; download script versioned.

## Done
- Repo scaffold (37 files) + PROJECT_INSTRUCTIONS.md + PROJECT_STATE.md.
- Claude Code config: `.claude/settings.json` (permissions/env/secret-deny),
  `.claude/settings.local.json.example`, `.gitignore` updated, `docs/SETUP_CLAUDE_CODE.md`.
- CLAUDE.md §0 (operating model + session protocol) added.

## Next action
0. **Silver built — review PR `feat/claims-silver`** (UC Claims — Phase 2 Silver). On merge → Gold.
1. ✅ DONE — Bronze ingestion notebook built + run on `prod_claims`: 4/5 tables loaded with exact
   counts (1000/15420/7366/26639); PII tagged; idempotent. Approved + committed + pushed (merged).
2. ⏸️ DEFERRED a few days (user): upload `FLAT_CMPL.txt` for `raw_complaints` (5th table).
3. ⏸️ DEFERRED a few days (user): verify PII tags (`information_schema.column_tags`).
4. ✅ DONE — Job `claims_bronze_ingest` created (resources/jobs.yml IaC + live API job_id
   1120539426174635). Serverless, 2 tasks (ingest → validate_row_counts), idempotent, 4/4 PASS.
5. PR "UC Claims — Phase 1 Bronze" under user review.
6. ✅ DONE — CI/CD fixed & GREEN. SP `drivepulse-cicd` (OAuth M2M) for CI/CD; GH secrets
   DATABRICKS_HOST/CLIENT_ID/CLIENT_SECRET set. Reconciled bundle (disabled dev_* scaffold →
   resources/*.disabled; claims job in resources/claims_bronze.yml). `bundle deploy -t dev`
   verified (job 899285954091552). Workflows pinned auth_type=oauth-m2m; push trigger fixed
   main→master. pyproject.toml fixes pytest src-layout.
7. NOTE: interim API job (1120539426174635) still exists alongside bundle-managed job — delete
   when fully on bundle. CD auto-runs on merge to master (deploy.yml).
8. (later) Event Hubs + prod workspace host; Policy/Telematics domains.

## Build target note
- Building directly against existing **`prod_claims`** catalog (has bronze/silver/gold schemas).
- Landing = user-created managed volume `prod_claims.bronze.claims_landing_zone` (ADLS-backed).
- Story model: **one story per source file**; user reviews each before moving on (user=approver, Claude=sr dev).

## Open questions / blockers
- [ ] Where do job-search skills currently live in Claude Code — global `~/.claude/skills/`,
      or already in a separate repo? (Determines whether step 2 of setup requires moving them.)
- [ ] (parked) Azure infra status in `rg_mission_2026_dataai` — needed at build-setup, not for design.
- [ ] (later) Trial cost ceiling; DE Pro cert target date, if any.

## Changelog
- **2026-06-25 s1** — Scaffold created and validated; operating model set; project instructions + state doc.
- **2026-06-25 s2** — Workflow finalized (drive + feature gates, A-spine/B-companion). Generated
  isolated Claude Code config (.claude/settings.json, local example, setup doc); added CLAUDE.md §0;
  corrected earlier claim about the isolation lock (it's managed-settings-only).
- **2026-06-25 s3** — Option 1 chosen (Claude drives via authenticated CLIs). Installed gh/az/
  databricks/python3.11. Azure login done; discovered existing premium workspace
  databricks_mission_2026_dataai (eastus) + shared RG inventory. Corrected CLAUDE.md §12
  (premium, not free/trial). Completed GitHub (bravichandra45) + Databricks (azure-cli profile
  `drivepulse`) auth; wired bundle dev host to real URL; `bundle validate` passes. Fully wired.
- **2026-06-26 s4** — Received + staged locked Claims package (architecture, user stories, data
  supply, bronze contract) under docs/claims + docs/contracts; created branch feat/claims-bronze.
  Wrote ADR 0002 (Claims locked + ADLS landing). Decided: source files land in ADLS `raw` container
  via external Volume (not UC-managed); repo PUBLIC. Updated CLAUDE.md §4/§5/§12, .gitignore,
  contract. Verified UC already has external location adls_dbx_external (file events on) on the lake.
- **2026-06-26 s5** — Built reusable dynamic Claims Bronze notebook (domains/claims/bronze/
  ingest_bronze.py): config-driven Auto Loader, string-safe, rescued data, ingest metadata,
  idempotent checkpoints, PII tags. Ran on prod_claims via serverless job — 4/5 tables loaded
  with exact row counts (complaints skipped, file not uploaded). Target switched to prod_claims
  (existing). Approved by user; committed + pushed.
- **2026-06-27 s6** — Extracted reusable row-count validator (validation/), tested all paths
  (PASS/FAIL-soft/FAIL-hard/schema), fixed a count-only type-inference bug. Created
  `claims_bronze_ingest` job: bundle IaC (resources/jobs.yml, serverless ingest→validate) +
  live API job (job_id 1120539426174635); verified end-to-end (idempotent, 4/4 PASS). Pointed
  bundle var catalog_claims→prod_claims. Confirmed full bundle deploy blocked (dev_* missing).
  Complaints + PII-tag verification deferred a few days per user. PR under review.
- **2026-06-29 s7** — Fixed CI/CD (both checks were red). test: added pyproject.toml
  (pytest pythonpath=src). validate/deploy: created CI/CD service principal `drivepulse-cicd`
  (workspace OAuth M2M via service-principal-secrets-proxy), set GH secrets, pinned
  DATABRICKS_AUTH_TYPE=oauth-m2m, fixed push trigger main→master. Reconciled bundle so deploy
  is clean: disabled dev_* scaffold (catalogs/pipelines/jobs → *.disabled), moved claims job to
  resources/claims_bronze.yml. CI now GREEN; `bundle deploy -t dev` verified (job 899285954091552).
- **2026-06-29 s8** — Built Claims SILVER as a Lakeflow Declarative Pipeline (ADR 0003):
  domains/claims/silver/claims_silver_pipeline.py + resources/claims_silver.yml. Deployed + ran
  (all 6 flows COMPLETED). Tables in prod_claims.silver: claim (16,100), claim_quarantine (320,
  all age_lt_16), claim_status_history (46,267), claim_severity (34,005), dim_policyholder (16,420
  SCD2), dim_vehicle (609 SCD2). Verified via validation/claims_silver_checks.py — all assertions
  pass (reconciliation, no overlap, severity match, SCD2 __START_AT/__END_AT, history coverage).
  Branch feat/claims-silver; PR open for review.
