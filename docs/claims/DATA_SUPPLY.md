# DrivePulse — Full Data Supply (per domain, all open & downloadable)

Rule: **one source file = one bronze table** (raw, as-is). A file that spans domains lands
ONCE in its owning domain; its other-domain columns are projected out in **silver**, not re-landed.

## UC1 — Policy  (`prod_policy`) — 3 bronze tables
| Bronze table | Source file | Origin / license | Scale | Contributes |
|---|---|---|---|---|
| `raw_policy_portfolio` | Motor_vehicle_insurance_data.csv | Mendeley, CC BY 4.0 | 105,555 | Real renewals/lapses → SCD2/CDC |
| `raw_policy_risk` | freMTPL2freq | OpenML id 41214 (open) | 677,991 | Risk features, BonusMalus, exposure |
| `raw_vehicle_recalls` | NHTSA Recalls (flat file / API) | US public domain | 30k+ | Recall campaigns → vehicle reference |

## UC2 — Claims  (`prod_claims`) — 3 bronze tables
| Bronze table | Source file | Origin / license | Scale | Contributes |
|---|---|---|---|---|
| `raw_claims_by_type` | sample_type_claim.csv | Mendeley, CC BY 4.0 | 7,366 | Claim cost by 9 types |
| `raw_claims_severity` | freMTPL2sev | OpenML id 41215 (open) | 26,444 | Claim amounts, one-to-many to policy |
| `raw_complaints` | FLAT_CMPL.zip | NHTSA, US public domain | millions (366MB) | Complaint narratives, VIN, crash/fire/injury → also RAG |

## UC3 — Telematics  (`prod_telematics`) — 3 (+1 optional) bronze tables
| Bronze table | Source file | Origin / license | Scale | Contributes |
|---|---|---|---|---|
| `raw_telematics_ubi` | telematics_syn.csv | UConn (So-Valdez), CC BY | 100,000 | Behavior features + shared policy/claims cols |
| `raw_trip_timeseries` | VED_DynamicData | GitHub gsoh/VED (open) | ~millions | Raw GPS+OBD-II time-series → STREAMING source |
| `raw_vehicle_static` | VED_StaticData | GitHub gsoh/VED (open) | 383 vehicles | Vehicle params → vehicle dimension |
| `raw_road_attributes` *(optional)* | eVED | Bitbucket (open) | 12M+ | Road elevation/speed-limit (or federate) |

## Join keys — real vs synthetic
- **Real, within a source:** Spanish (`ID`), freMTPL2 (`IDpol`), So-Valdez (per-row), VED (`VehId`/`Trip`).
- **Synthetic bridges (documented, deterministic seed):** link the separate portfolios
  (Spanish ↔ freMTPL2 ↔ So-Valdez) and map VED `VehId` → a policy/vehicle. Disclosed in README.

## Why this is real engineering (not a toy)
- **Silver conforms multiple feeds:** two policy portfolios → one `dim_policy`; three claims feeds
  → one conformed `fact_claim`; telematics features + raw trips + vehicle static → trip facts + `dim_vehicle`.
- **Every pattern is exercised:** Auto Loader (batch CSVs), streaming (VED→Event Hubs), federation
  (recalls/road attrs), SCD2 (policy renewals), CDC (claim/complaint status), governance (VIN/PII), RAG (complaint narratives).

## Download methods (all no-login)
- Mendeley: direct file URLs (already retrieved).
- OpenML: `fetch_openml(data_id=41214)` and `41215`.
- UConn: direct CSV `https://www2.math.uconn.edu/~valdez/telematics_syn-032021.csv`.
- NHTSA: `https://static.nhtsa.gov/odi/ffdd/cmpl/FLAT_CMPL.zip` (+ recalls flat file / Recalls API).
- VED: GitHub `gsoh/VED` (raw files / 7z); eVED via Bitbucket clone.
