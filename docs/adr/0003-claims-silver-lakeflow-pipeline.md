# ADR 0003 — Claims Silver as a Lakeflow Declarative Pipeline

**Status:** accepted
**Date:** 2026-06-29

## Context
Silver must conform/clean/dedupe Bronze, enforce expectations with quarantine, derive a claim
lifecycle (CDC), and build SCD2 dims. The pattern-coverage map (CLAUDE.md §3) requires Lakeflow
Declarative Pipelines, SCD2 via `APPLY CHANGES INTO`, and CDC — Silver is where these first land.

## Decision
Build Claims Silver as **one Lakeflow Declarative Pipeline** (`resources/claims_silver.yml`,
serverless, notebook `domains/claims/silver/claims_silver_pipeline.py`) targeting
`prod_claims.silver`. Tables (mapped to EPIC 2 stories):
- **S1** `claim` — conform `raw_insurance_claims` + `raw_carclaims` into one grain; typed; deduped
  on a surrogate `claim_id`; `source_system`; unified `fraud`.
- **S3** `claim_quarantine` — rows failing expectations (amount ≥ 0, valid type, age ≥ 16, dates
  ordered) routed out **with a reason**; nothing dropped. Done as a conformed view split into
  `claim` (valid) / `claim_quarantine` (invalid), plus `@dlt.expect_all` metrics.
- **S2** `claim_status_history` — one row per status transition (FNOL → under_review → terminal).
- **S4** `dim_policyholder`, `dim_vehicle` — SCD2 via `dlt.apply_changes(stored_as_scd_type=2)`.
- `claim_severity` — conform `freMTPL2sev` + Spanish by-type.

**Lifecycle is synthetic & deterministic:** `fnol_date`, `claim_status`, `settlement_date`,
`cycle_time_days` are seeded by a hash of `claim_id` (reproducible, no RNG). carclaims `incident_date`
is synthesized from `Year`+`Month` (flagged `incident_date_is_synthetic`). Documented per ADR 0002.

## Consequences
- Re-enables a bundle pipeline resource (Bronze had disabled the stub `pipelines.yml`).
- Verified on real data: claim 16,100 + quarantine 320 = 16,420 (= bronze total; quarantine all
  `age_lt_16`); claim_severity 34,005; SCD2 dims carry `__START_AT`/`__END_AT`.
- carclaims has no money columns → claim amounts null for those rows (documented gap).
- A live SCD2 **version-2** example is not fabricated into the locked Bronze (would break Bronze
  row-count DoD); the mechanism is in place and triggers on changed source records.
- `silver.complaint` deferred until the NHTSA complaints file is ingested.
