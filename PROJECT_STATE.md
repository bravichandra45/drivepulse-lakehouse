# PROJECT_STATE — DrivePulse Lakehouse
_Last updated: 2026-06-26 · session 4 · by Claude_

> Read this first every session. Update it last every session.

## Current phase
**Phase 1 — Claims Bronze.** Claims architecture LOCKED (ADR 0002). Working on branch
`feat/claims-bronze`, catalog `dev_claims`. Goal: 5 sources → 5 `raw_*` bronze tables via Auto
Loader from **ADLS landing**, PII tags, validate row counts, open PR, **STOP at review gate**
(no silver/gold). Environment fully wired (see audit below).

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
1. ✅ DONE — CLI auth + bundle validated; Claims package staged; docs/ADR updated; public repo decided.
2. **Push `feat/claims-bronze` to new public `origin`.**
3. **Run live Bronze build** (awaiting go): create `dev_claims` + bronze schema; external Volume
   `bronze.landing` on ADLS; download 366MB NHTSA complaints; upload 5 sources to ADLS; Auto Loader
   → 5 `raw_*` tables; PII tags; validate row counts (1000/15420/7366/26639/complaints) + samples.
4. Open PR "UC Claims — Phase 1 Bronze"; update PROJECT_STATE + SESSION_LOG; **STOP for review**.
5. (later) provision Event Hubs + prod workspace host; Policy/Telematics domains.

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
