# SESSION_LOG — DrivePulse Lakehouse

> Append-only narrative log of work sessions. Newest entry at the bottom.
> `PROJECT_STATE.md` stays the short "where we are now" file — this is the long-form history.

---

## 2026-06-26 · Session 3 — Environment setup & infra analysis

**Goal:** Adopt Option 1 (Claude drives via authenticated CLIs; user provides browser logins).
Review current state across repo + GitHub + Azure + Databricks, wire everything up, keep docs current.

### Tooling installed (via winget)
Machine had only `git` + a Python stub. Installed:
- GitHub CLI `gh` 2.95.0
- Azure CLI `az` 2.87.0
- Databricks CLI 1.5.0
- Python 3.11.9

### Authentication — all three surfaces wired
- **Azure** ✅ — device-code login (completed in Chrome). Account
  `balantrapu.ravichandra@gmail.com`, "Azure subscription 1" (`93a8c829…`), tenant `2bb692f9…`. Admin.
- **GitHub** ✅ — `gh auth login` as `bravichandra45`; token in Windows keyring;
  scopes `repo`, `workflow`, `read:org`, `gist`.
- **Databricks** ✅ — `~/.databrickscfg` profile `drivepulse` using `auth_type = azure-cli`
  (reuses the az token — no PAT, no workspace browser login). User is a workspace **admin**
  (allow-cluster-create).

**Learnings:**
- Browser/device login flows are flaky in this sandboxed setup; azure-cli passthrough is the
  reliable path for Databricks.
- Claude's shell commands run **sandboxed without network** by default; cloud-touching calls
  (az/databricks/gh against their APIs) need the sandbox disabled per-invocation.
- `DATABRICKS_CONFIG_PROFILE=drivepulse` is set in `.claude/settings.json`, so the profile must
  be named `drivepulse` (not `DEFAULT`).

### Infrastructure analysis (verified via `az`)
**Workspace (exists, healthy):** `databricks_mission_2026_dataai` · premium · East US ·
state Succeeded · URL `adb-7405605467002690.10.azuredatabricks.net`.

**Resource group `rg_mission_2026_dataai` inventory:**

| Resource | Type | Region | Ours? |
|---|---|---|---|
| `databricks_mission_2026_dataai` | Databricks workspace | eastus | yes |
| `adls4missiondataai` | ADLS Gen2 storage | eastus | yes — our lake |
| `adls_connect_databricks` | Databricks access connector | eastus | yes — UC→ADLS identity |
| `adls_connect_databricks_finanace` | Databricks access connector | eastus | no — finance mission |
| `adlsfinancemission2026` | Storage | eastasia | no — finance mission |
| `app-mission-sql` (+ `app_mission_db`) | Azure SQL server + DB | eastasia | no — other app |

**Three findings that mattered:**
1. **Shared RG** — a parallel "finance mission" + a SQL app share `rg_mission_2026_dataai`.
   Rule: touch only DrivePulse resources; prefix anything new `drivepulse_*`; never modify finance/SQL.
2. **No Event Hubs namespace yet** — required later for telematics streaming.
3. **Workspace is premium, not free/trial** — old docs were wrong. Premium is good: it enables
   row filters, column masks, and serverless that the governance patterns need.

### Bundle wired & validated
- Set `databricks.yml` **dev** workspace host to the real URL (was `REPLACE_ME`).
- `databricks bundle validate` PASSES against the workspace (only 4 harmless `sync.exclude`
  pattern warnings).
- `prod` host still `REPLACE_ME` — no separate prod workspace exists yet.

### Docs updated (show-then-apply rule)
- **CLAUDE.md §12** — corrected free/trial → premium; added real workspace URL/subscription;
  flagged the shared resource group.
- **PROJECT_STATE.md** — added verified s3 environment audit; updated Next action + Changelog.

### Git checkpoints (branch `master`, no remote yet)
- `ee09670` — docs: record verified Azure/Databricks environment + CLI auth state
- `e5faac4` — chore: wire bundle to real workspace; mark environment fully authenticated

### State at end of session
- ✅ Environment fully stood up & verified: tooling, auth, infra mapped, bundle validated, docs current.
- Open (not blocking): repo is local-only (never pushed); Event Hubs not provisioned; all domain
  code is still scaffold/stubs; **new architecture / sources / requirements to be locked shortly**
  — current CLAUDE.md design is provisional until that lock.
- Next: user drops new requirements → propose doc changes → approve → re-baseline → build
  (bootstrap UC → telematics vertical slice first).

---

## 2026-06-26 · Session 5 — Claims Bronze build (Story: dynamic ingestion)

**Goal:** Build Claims Bronze ingestion. Operating model reaffirmed: user = approver,
Claude = senior developer writing all code; one story at a time; target the existing
`prod_claims` catalog (not `dev_claims`); user creates the ADLS landing zone.

### What was built
- Single **reusable, config-driven** notebook `domains/claims/bronze/ingest_bronze.py`:
  a `SOURCES` registry (one entry per source file) + generic Auto Loader (`cloudFiles`) logic.
- String-safe ingest (`inferColumnTypes=false`), `schemaEvolutionMode=rescue` +
  `_rescued_data`, per-source `sep`/`header`, `pathGlobFilter` to isolate each file.
- Ingest metadata on every row: `_ingest_ts`, `_source_file`, `_batch_id`, `_rescued_data`.
- Append-only managed Delta via `toTable`, per-table checkpoints in auto-created volume
  `prod_claims.bronze.checkpoints`, `trigger(availableNow=True)` → idempotent (US-B3).
- PII columns tagged in UC (`SET TAGS ('pii'='true')`), **not masked** (US-B2).
- Returns counts via `dbutils.notebook.exit(json)`.

### Landing zone (user-created)
- UC managed volume `prod_claims.bronze.claims_landing_zone`, ADLS-backed
  (`abfss://raw@adls4missiondataai…/__unitystorage/…`). User uploaded 4 CSVs + the download script.

### Run + result (serverless one-time job submit → SUCCESS)
| Table | Rows | Expected |
|---|---|---|
| `prod_claims.bronze.raw_insurance_claims` | 1,000 | 1,000 ✅ |
| `prod_claims.bronze.raw_carclaims` | 15,420 | 15,420 ✅ |
| `prod_claims.bronze.raw_claims_by_type` | 7,366 | 7,366 ✅ |
| `prod_claims.bronze.raw_claim_severity` | 26,639 | 26,639 ✅ |
| `prod_claims.bronze.raw_complaints` | — | skipped — `FLAT_CMPL.txt` not uploaded yet |

Execution path: wrote notebook in repo → imported to workspace
`/Users/balantrapu.ravichandra@gmail.com/drivepulse/ingest_bronze` → `databricks jobs submit`
(serverless, no-wait) → polled `get-run` → `get-run-output` for counts.

### Open / next (resume tomorrow)
- Upload `FLAT_CMPL.txt` (~366MB, `download_all_sources.py --big`) → re-run for `raw_complaints`.
- Verify PII tags visible (`information_schema.column_tags`).
- Bundle-ify the run as a job in `resources/jobs.yml` (replace manual import).
- Then open PR "UC Claims — Phase 1 Bronze" at the review gate.

---

## 2026-06-29 · Session 8 — Claims Silver (all EPIC-2 stories)

**Goal:** Build & test all Silver stories. Engine locked: **Lakeflow Declarative Pipeline** (ADR 0003);
granularity per-user-story; target `prod_claims`.

### Built
- `domains/claims/silver/claims_silver_pipeline.py` (DLT) + `resources/claims_silver.yml` (serverless pipeline).
- Tables in `prod_claims.silver`: `claim`, `claim_quarantine`, `claim_status_history`,
  `claim_severity`, `dim_policyholder` (SCD2), `dim_vehicle` (SCD2).
- S1 conform (insurance_claims + carclaims → one grain, typed, deduped, surrogate `claim_id`).
- S2 seeded synthetic lifecycle (fnol/status/settlement/cycle_time) + status-history transitions.
- S3 expectations → quarantine (amount≥0, valid type, age≥16, dates ordered); nothing dropped.
- S4 SCD2 dims via `apply_changes(stored_as_scd_type=2)`.

### Tested (validation/claims_silver_checks.py — all assertions pass)
| Table | Rows |
|---|---|
| claim | 16,100 |
| claim_quarantine | 320 (all `age_lt_16`) |
| claim_status_history | 46,267 (covers all 16,100 claims) |
| claim_severity | 34,005 (= 26,639 + 7,366) |
| dim_policyholder (SCD2) | 16,420 |
| dim_vehicle (SCD2) | 609 |

Reconciliation: claim + quarantine = 16,420 = bronze total (1000+15420), 0 dupes, no overlap.
SCD2 dims carry `__START_AT`/`__END_AT`; current = distinct keys. Quarantine path proven on real
failing rows (320 age<16). DLT run: all 6 flows COMPLETED.

### Deferred / notes
- `silver.complaint` — needs the NHTSA complaints bronze table (parked).
- SCD2 version-2 example not fabricated into locked Bronze (would break row-count DoD); mechanism in place.
- Branch `feat/claims-silver`; PR opened for review. On merge → Gold (EPIC 3).

---

## 2026-06-29 · Session 9 — Claims Gold (all EPIC-3 stories)

**Goal:** Build & test all Gold stories. Engine: Lakeflow pipeline (ADR 0004), target `prod_claims.gold`.

### Built (`domains/claims/gold/claims_gold_pipeline.py` + `resources/claims_gold.yml`)
- **Dims:** dim_date (7,781), dim_claim_status, dim_claim_type, dim_geography, dim_incident,
  dim_policyholder (16,420, current from silver SCD2), dim_vehicle (609).
- **Facts:** fact_claim (16,100; dim keys + measures + denormalized descriptive attrs),
  fact_claim_lifecycle (accumulating snapshot), fact_claim_status_history (46,267).
- **Marts:** mart_claims_kpi (US-G1, by source_system), mart_fraud_signals (US-G2, 35 rows:
  make/severity/claim_type), feature_fraud (US-G3, 16,100, no outcome leakage).

### Tested (`validation/claims_gold_checks.py` — all assertions pass)
- fact_claim = silver.claim = 16,100; lifecycle = 16,100; status_history = 46,267; feature_fraud = 16,100.
- Referential integrity: 0 orphan dim keys (status/claim_type/geography/incident).
- mart_claims_kpi reconciles: Σ claim_count 16,100 = fact_claim; Σ fraud 1,139 = fact fraud sum.
- feature_fraud has label, no leakage columns.
- Caught & fixed a notebook bug: a missing `# COMMAND ----------` made the checks notebook run as
  one markdown cell (SUCCESS but no Python executed) — re-ran after fix to genuinely validate.

### Deferred / notes
- `loss_ratio` & `claim_frequency` null — need premium/exposure from the Policy domain (cross-domain).
- `fact_complaint` deferred with the complaints source.
- Branch `feat/claims-gold` (stacked on `feat/claims-silver`); PR opened. Next: ML (EPIC 4), GenAI (EPIC 5).
