# PROJECT_STATE — DrivePulse Lakehouse
_Last updated: 2026-06-25 · session 2 · by Claude_

> Read this first every session. Update it last every session.

## Current phase
**Phase 0 — setup.** Operating model + workflow locked. Isolated Claude Code project config
generated. Next: stand up the project in Claude Code (per docs/SETUP_CLAUDE_CODE.md), then
begin architecture design at Topic 1 (System context & boundary).

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
1. User stands up the isolated project in Claude Code (docs/SETUP_CLAUDE_CODE.md) + verifies
   job-search skills don't bleed in.
2. Then begin **architecture design — Topic 1: System context & boundary** (actors, external
   systems, in/out of scope). No build code until design + agile plan are agreed.

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
