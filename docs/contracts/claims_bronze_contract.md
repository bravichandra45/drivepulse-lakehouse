# Claims · Phase 1 — Bronze Requirement Contract

Catalog `dev_claims`. Pattern: Auto Loader batch from UC Volume `dev_claims.bronze.landing`.
All tables append-only, as-is, + `_ingest_ts`, `_source_file`, `_batch_id`, `_rescued_data`.

| Bronze table | Source file | Format | Rows | Key columns | PII to TAG |
|---|---|---|---|---|---|
| `raw_insurance_claims` | insurance_claims.csv | CSV `,` | 1,000 | policy_number, incident_date, incident_type, severity, total/injury/property/vehicle_claim, auto_make/model/year, **fraud_reported** | policy_number, insured_zip, incident_location |
| `raw_carclaims` | carclaims.csv | CSV `,` | 15,420 | Make, Fault, PolicyType, VehicleCategory, Days:Policy-Accident/Claim, MonthClaimed, **FraudFound** | PolicyNumber |
| `raw_claims_by_type` | sample_type_claim.csv | CSV `;` | 7,366 | ID, Cost_claims_year, Cost_claims_by_type, Claims_type | ID (policy link) |
| `raw_claim_severity` | freMTPL2sev.csv | CSV `,` | 26,639 | IDpol, ClaimAmount | IDpol (policy link) |
| `raw_complaints` | FLAT_CMPL.txt | TAB, fixed layout (CMPL.txt) | millions | MAKETXT, MODELTXT, YEARTXT, CRASH, FIRE, INJURED, DEATHS, FAILDATE, VIN, CDESCR (narrative) | VIN, CITY, STATE |

## Rules
- Zero transforms; keep source types (string-safe). Drop nothing.
- Delimiters per table (note Spanish `;`). NHTSA complaints is tab-delimited, fixed layout — see CMPL.txt; `_c39` junk column in insurance_claims is kept as-is.
- Land local CSVs to `dev_claims.bronze.landing` (UC Volume); Auto Loader reads from there.
- Tag PII columns in Unity Catalog; **do not mask**.
- Idempotent + checkpointed (`trigger(availableNow=True)`).

## Data location
Local files in `./data/claims/`. NHTSA complaints (~366MB) via
`python data/claims/download_all_sources.py --big`.

## Definition of Done (gate)
5 `raw_*` tables; row counts match; metadata + PII tags present; 5-row sample of each shown;
contract committed; PROJECT_STATE + SESSION_LOG updated; **PR opened** for review.
