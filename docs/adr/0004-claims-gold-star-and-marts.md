# ADR 0004 — Claims Gold: Kimball star + marts (Lakeflow)

**Status:** accepted
**Date:** 2026-06-29

## Context
Gold must present a Kimball star (conformed dims + facts) and the marts that agents/BI query
(KPIs, fraud signals, ML features) — EPIC 3 (US-G1..G3).

## Decision
Build Claims Gold as a **Lakeflow Declarative Pipeline** (`resources/claims_gold.yml`, serverless,
`domains/claims/gold/claims_gold_pipeline.py`) reading `prod_claims.silver` → `prod_claims.gold`:
- **Dims:** `dim_date`, `dim_claim_status`, `dim_claim_type`, `dim_geography`, `dim_incident`,
  `dim_policyholder` / `dim_vehicle` (current rows from the silver SCD2 dims). Surrogate keys =
  `sha2` of natural keys.
- **Facts:** `fact_claim` (one per claim; dim keys + measures + a few denormalized descriptive
  attrs so marts are self-contained), `fact_claim_lifecycle` (accumulating snapshot: milestone
  dates, stage lags, cycle time), `fact_claim_status_history` (one per status change).
- **Marts:** `mart_claims_kpi` (US-G1), `mart_fraud_signals` (US-G2), `feature_fraud` (US-G3,
  outcome-leakage columns excluded).

## Consequences
- Verified: fact_claim 16,100 (= silver.claim); RI 0 orphan keys; mart_claims_kpi reconciles
  (Σ claim_count 16,100, Σ fraud 1,139 = fact); feature_fraud no leakage; dims populated.
- **`loss_ratio` and `claim_frequency` are null** — they need premium / exposure from the Policy
  domain (cross-domain). Documented gap; fill when UC Policy lands.
- `fact_complaint` deferred with the complaints source.
- ML model training (US-M*) and the GenAI copilot (US-AI1) build on `feature_fraud` / gold later.
