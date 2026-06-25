# DrivePulse Architecture

## The mesh
Three Unity Catalog catalogs, each owned by one team, each a self-contained data product.
Producers publish gold tables; consumers read them by three-part name. No copying.

| Catalog | Team | Owns |
|---|---|---|
| `prod_telematics` | Connected Vehicle / IoT | trips, telemetry events, driver behavior |
| `prod_policy` | Underwriting | policies, drivers, vehicles-on-policy, coverages, vehicle ref |
| `prod_claims` | Claims Operations | claims, FNOL, status history, payments |

## Data flow
1. **Ingest** — Event Hubs (telemetry stream) + Auto Loader (policy/claims/recall batch).
2. **Bronze** — raw, append-only, checkpointed.
3. **Silver** — Lakeflow Declarative Pipelines: expectations + quarantine, SCD2 dims, CDC.
4. **Gold** — Kimball stars + cross-domain marts.
5. **Docs** — chunked text + embeddings → Vector Search.
6. **Agents** — Mosaic AI, served endpoints, MLflow eval. Read gold/docs only.

## Federation (never ingested)
- Weather → Postgres
- NHTSA vPIC → Postgres / SQL Server
- OpenStreetMap road network → PostGIS

## Why this is a mesh and not a lake
Ownership boundaries are real (three teams), storage is separated by catalog, and the only
way one domain uses another's data is through its published gold contract. That contract +
ownership + self-serve medallion = mesh.

## Diagram
TODO(claude-code): add a hero architecture diagram to docs/images/ and embed it in README.
