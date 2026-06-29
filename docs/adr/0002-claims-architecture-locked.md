# ADR 0002 — Claims domain architecture locked ("Claims Intelligence & Fraud")

**Status:** accepted
**Date:** 2026-06-26

## Context
The Claims domain needed a concrete, buildable spec: real open datasets, a medallion path to
ML + a GenAI adjuster copilot, and a Phase-1 scope we can ship behind a review gate. We also
decided how raw files physically land.

## Decision
Adopt the locked Claims architecture (`docs/claims/CLAIMS_ARCHITECTURE.md`):
5 sources → 5 bronze `raw_*` tables (`dev_claims.bronze`) → conformed silver (claim,
claim_severity, complaint, derived status-history CDC, quarantine, 7 dims) → gold star
(`fact_claim`, `fact_claim_lifecycle` accumulating snapshot, `fact_claim_status_history`,
`fact_complaint`) + marts (`mart_claims_kpi`, `mart_fraud_signals`, `feature_fraud`) → ML + RAG copilot.
Lifecycle status/dates are derived/synthetic (seeded, documented). Build phase-by-phase, Bronze
first, each phase gated by PR review.

**Raw landing in ADLS:** source files land in the ADLS `raw` container
(`abfss://raw@adls4missiondataai.dfs.core.windows.net/claims/landing/`), exposed through an
**external** UC Volume `dev_claims.bronze.landing` (storage credential `adls_dbx_cred` /
external location `adls_dbx_external`, file events enabled). No UC-managed volume for landing.
Uploads go through Databricks' managed identity (the `az` login lacks `Storage Blob Data *` RBAC).

## Consequences
- Claims sources change from CLAUDE.md's original Allstate set to insurance_claims / carclaims /
  sample_type_claim / freMTPL2sev / NHTSA complaints (see `docs/claims/DATA_SUPPLY.md`).
- Files live in the lake; Auto Loader gets file-notification mode for free (events already on).
- Exercises Auto Loader, SCD2, CDC, governance, ML, and RAG within one domain.
- Some KPIs (true claim frequency) need cross-domain policy exposure — approximated until UC Policy lands.
