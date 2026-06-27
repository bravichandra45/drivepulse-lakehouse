# Claims Domain — Architecture (LOCKED)

**Use case:** "Claims Intelligence & Fraud" — analytics + fraud + an adjuster copilot.
**Catalog:** `dev_claims` (prod: `prod_claims`). Medallion: bronze → silver → gold → ML/GenAI.

## End-to-end flow
```mermaid
flowchart LR
  subgraph SRC[5 Sources]
    A[insurance_claims 1k]
    B[carclaims 15k]
    C[claims_by_type 7k]
    D[freMTPL2sev 27k]
    E[NHTSA complaints]
  end
  subgraph BRZ[Bronze raw]
    RB1[raw_insurance_claims]
    RB2[raw_carclaims]
    RB3[raw_claims_by_type]
    RB4[raw_claim_severity]
    RB5[raw_complaints]
  end
  subgraph SLV[Silver conformed]
    S1[silver.claim]
    S2[silver.claim_severity]
    S3[silver.complaint]
    SH[claim_status_history CDC]
    SQ[claim_quarantine]
    SD[dims: policyholder vehicle incident claim_type geography status date]
  end
  subgraph GLD[Gold star + marts]
    F1[fact_claim]
    F2[fact_claim_lifecycle - accumulating snapshot]
    F3[fact_claim_status_history]
    F4[fact_complaint]
    M1[mart_claims_kpi]
    M2[mart_fraud_signals]
    M3[feature_fraud - ML]
  end
  subgraph USE[Consumption]
    K[KPIs: loss ratio, frequency, severity, fraud rate, cycle time]
    ML[ML: fraud + severity]
    AI[GenAI: adjuster copilot]
  end
  A-->RB1
  B-->RB2
  C-->RB3
  D-->RB4
  E-->RB5
  RB1-->S1
  RB2-->S1
  RB3-->S2
  RB4-->S2
  RB5-->S3
  S1-->SD
  S1-->SH
  S1-->F1
  S1-->F2
  SH-->F3
  S3-->F4
  SD-->F1
  F1-->M1
  F1-->M2
  F1-->M3
  M1-->K
  M3-->ML
  F4-->AI
  S3-->AI
```

## Silver (LOCKED)
- `silver.claim` — conform insurance_claims + carclaims into one claim grain (+ `source_system`, `fraud` flag, dedup, typed).
- `silver.claim_severity` — freMTPL2sev + Spanish by-type (claim amount + type, portfolio scale).
- `silver.complaint` — NHTSA narratives + crash/fire/injury flags; narrative text extracted for RAG.
- `silver.claim_status_history` — **derived** lifecycle (CDC): FNOL → under-review → approved/denied → settled → closed.
- `silver.claim_quarantine` — rows failing expectations.
- **Custom derivation logic (seeded, documented as synthetic):** `fnol_date`, `claim_status`,
  `settlement_date`, `cycle_time_days` from `incident_date` + severity + fraud + (carclaims timing fields).

## Gold — dimensions (LOCKED)
`dim_policyholder` (SCD2), `dim_vehicle` (SCD2), `dim_incident`, `dim_claim_type`, `dim_geography`,
`dim_claim_status`, `dim_date`.

## Gold — facts (LOCKED)
- `fact_claim` — grain: one claim. Measures: total/injury/property/vehicle amount, is_fraud, claim_count.
- `fact_claim_lifecycle` — **accumulating snapshot**: milestone dates + stage lags + cycle_time. Powers cycle-time KPIs.
- `fact_claim_status_history` — one row per status change.
- `fact_complaint` — one row per NHTSA complaint.

## Gold — marts & KPIs (LOCKED)
- `mart_claims_kpi`: loss ratio, claim frequency, severity, **fraud rate**, claim mix, component split, **avg cycle time, open vs closed, aging, denial rate**.
- `mart_fraud_signals`: fraud rate by make / severity / hobby / incident type.
- `feature_fraud`: ML feature table.

## ML & GenAI (later phases)
- **ML:** fraud classifier + severity predictor on `feature_fraud`.
- **GenAI:** Claims Adjuster Copilot — summarize claim, find similar, flag fraud, draft assessment; RAG over `silver.complaint`.

## Known gaps (handled in silver, documented)
1. Lifecycle status + dates are **derived/synthetic** (seeded).
2. carclaims has no money column → amounts null for those rows (fraud/categorical only).
3. True claim frequency needs policy exposure (cross-domain with UC Policy) — approximate until then.
