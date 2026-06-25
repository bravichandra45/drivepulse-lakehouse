# PROJECT_STATE — DrivePulse Lakehouse
_Last updated: 2026-06-25 · session 2 · by Claude_

> Read this first every session. Update it last every session.

## Current phase
**Phase 0 — setup.** Operating model + workflow locked. Isolated Claude Code project config
generated. Next: stand up the project in Claude Code (per docs/SETUP_CLAUDE_CODE.md), then
begin architecture design at Topic 1 (System context & boundary).

## Environment audit (2026-06-25, s3) — VERIFIED
- Tooling: git, gh, az, databricks (CLI 1.5.0), python 3.11 all installed on this machine.
- Auth: Azure ✅ (balantrapu.ravichandra@gmail.com · "Azure subscription 1" 93a8c829… ·
  tenant 2bb692f9…). GitHub ✅ (bravichandra45, keyring; scopes repo/workflow/read:org/gist).
  Databricks profile ❌ pending.
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

## Done
- Repo scaffold (37 files) + PROJECT_INSTRUCTIONS.md + PROJECT_STATE.md.
- Claude Code config: `.claude/settings.json` (permissions/env/secret-deny),
  `.claude/settings.local.json.example`, `.gitignore` updated, `docs/SETUP_CLAUDE_CODE.md`.
- CLAUDE.md §0 (operating model + session protocol) added.

## Next action
1. Finish CLI auth: GitHub (`gh auth login`) + Databricks profile
   (`databricks auth login --host adb-7405605467002690.10.azuredatabricks.net`).
   Then set bundle `host` to the real URL and run `databricks bundle validate`.
2. (pending user) NEW architecture / sources / requirements to be locked shortly — "a lot will
   change." Treat current CLAUDE.md architecture as provisional until that lock.
3. Then architecture design topics + agile plan. No build code until design is agreed.

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
  (premium, not free/trial). GitHub + Databricks auth still pending.
