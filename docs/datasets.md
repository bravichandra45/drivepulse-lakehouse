# Datasets — sources, scale, and where each lands

All public. Volume floor: >= 50k records per domain. Telemetry replayed to billions of
stream events for large-scale processing demos.

## Telematics  → prod_telematics.bronze (streaming) / data/telematics
- **Vehicle Energy Dataset (VED)** — ~383 vehicles, OBD-II + GPS, U-Michigan/Argonne/INL.
- **Extended VED (eVED)** — 12M+ road elevation / speed-limit / direction records.
- **UAH-DriveSet**, **comma2k19** (33h CA driving) — additional behavior signals.

## Policy  → prod_policy.bronze (Auto Loader) / data/policy
- **Porto Seguro Safe Driver Prediction** (Kaggle) — ~595k train rows, 57 features.
- Kaggle "Vehicle Insurance" / "Insurance Claims and Policy" sets — supplementary.

## Claims  → prod_claims.bronze (Auto Loader) / data/claims
- **Allstate Claims Severity** (Kaggle 2016) — ~188k claim rows with loss values.
- **Allstate Claim Prediction Challenge** — larger, for volume.

## Vehicle reference  → prod_policy (or federated)
- **NHTSA vPIC** — downloadable Postgres / SQL Server DBs (all VINs 1980+).
- **NHTSA Recalls API** — 30k+ recalls back to 1949.

## Crash & safety  → federated / prod_claims
- **NHTSA FARS** — ~989k fatalities since 1975, 40 tables (BigQuery + ZIP).
- **NHTSA ODI complaints** — narrative text (also feeds the docs RAG corpus).

## Environment (federation only — never ingest)
- **NOAA GHCN-Daily** weather → Postgres
- **OpenStreetMap** → PostGIS
- **FHWA HPMS** AADT traffic volume

## Documents (RAG)  → *.docs schemas
- NHTSA recall notification letters (PDF) → prod_telematics.docs
- State DOI sample auto-policy forms (CA/NY/TX) → prod_policy.docs
- NHTSA VOQ / ODI complaint narratives → prod_claims.docs

## Synthetic linking (be transparent about this)
No public dataset joins telematics→policy→claim. Generate deterministic join keys with
Faker + a fixed seed so VED vehicles map to Porto Seguro policies map to Allstate claims.
Document the mapping logic and seed so results are reproducible.
