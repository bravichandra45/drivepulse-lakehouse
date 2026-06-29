# Claims Domain — User Stories

Format: As a **role**, I want **goal**, so that **benefit**. AC = acceptance criteria.

## EPIC 1 — Bronze (raw ingestion)  ← we build this first
**US-B1** — As a *data engineer*, I want all 5 claim sources landed as-is into `dev_claims.bronze`,
so that no raw data is lost and lineage starts clean.
- AC: 5 `raw_*` tables exist; row counts = 1000 / 15420 / 7366 / 26639 / complaints; each row has
  `_ingest_ts`, `_source_file`, `_batch_id`, `_rescued_data`; no transforms applied.

**US-B2** — As a *data governance lead*, I want PII columns tagged at bronze, so that masking can be
enforced later without re-scanning.
- AC: insured_zip, policy_number, incident_location, VIN, age/dob-like columns carry a PII tag; nothing masked yet.

**US-B3** — As a *data engineer*, I want ingestion to be idempotent, so that re-runs don't duplicate rows.
- AC: Auto Loader checkpointed; second run adds 0 rows.

## EPIC 2 — Silver (conform + derive)
**US-S1** — As a *data engineer*, I want the two fraud files conformed into one `silver.claim`, so that
fraud analytics span both populations.
- AC: common schema + `source_system`; deduped; typed; row count = sum minus dupes; reconciliation logged.

**US-S2** — As a *claims analyst*, I want a derived claim **lifecycle** (status + FNOL/settlement dates),
so that I can measure how fast claims close.
- AC: `claim_status`, `fnol_date`, `settlement_date`, `cycle_time_days` populated by seeded logic;
  `silver.claim_status_history` has one row per transition; logic documented as synthetic.

**US-S3** — As a *data steward*, I want bad rows quarantined not dropped, so that nothing disappears silently.
- AC: expectations (amount ≥ 0, valid type, age ≥ 16, dates ordered) route failures to `claim_quarantine` with a reason.

**US-S4** — As a *BI developer*, I want SCD2 dims for policyholder & vehicle, so that history is preserved.
- AC: `effective_from/to`, `is_current`; a worked example shows a versioned change.

## EPIC 3 — Gold (model + KPIs)
**US-G1** — As a *claims manager*, I want a KPI mart, so that I can see loss ratio, frequency, severity,
fraud rate, claim mix, and cycle time by segment and period.
- AC: `mart_claims_kpi` returns each KPI; numbers reconcile to fact_claim.

**US-G2** — As a *fraud investigator*, I want fraud-signal breakdowns, so that I can target reviews.
- AC: `mart_fraud_signals` gives fraud rate by make / severity / incident type.

**US-G3** — As a *data scientist*, I want an ML-ready feature table, so that I can train a fraud model.
- AC: `feature_fraud` one row per claim, encoded features + label, no leakage columns.

## EPIC 4 — ML
**US-M1** — As a *fraud investigator*, I want a fraud-likelihood score per claim, so that I can prioritize.
- AC: classifier trained on `feature_fraud`; AUC reported; scores written to a gold table; MLflow run logged.

**US-M2** — As a *pricing analyst*, I want claim-severity prediction, so that reserves are better estimated.
- AC: regression model; error metric reported; MLflow run logged.

## EPIC 5 — GenAI
**US-AI1** — As a *claims adjuster*, I want a copilot that summarizes a claim and flags fraud signals,
so that I handle cases faster.
- AC: agent reads gold + `silver.complaint`; returns summary + similar claims + fraud flags + draft note;
  grounded (citations); evaluated with MLflow Agent Eval.
