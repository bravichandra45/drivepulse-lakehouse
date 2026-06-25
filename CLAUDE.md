# CLAUDE.md — DrivePulse Lakehouse

> This file is the single source of truth for Claude Code. Read it fully at the start of
> every session before writing or changing anything. If a request conflicts with this
> file, stop and ask. Keep this file updated as the architecture evolves.

---

## 0. Operating model & session protocol

**Claude drives; the user reviews.** Set the agenda, make decisions, produce the work. Stop
to ask only when genuinely blocked, when a decision is the user's (cost, scope, business
judgment), or when an action needs them (Azure portal, GitHub, credentials).

**One feature at a time, with approval gates.** For each feature: discuss → user gives
direction → develop → user approves → close it (update PROJECT_STATE.md; write an ADR if it
was an architecture decision) → next. Don't bundle features or run ahead of approval.

**Session protocol — every session:**
1. **Start:** read `PROJECT_STATE.md`; restate the current phase and the immediate next action in 1–2 lines.
2. Do the work.
3. **End:** update `PROJECT_STATE.md` (what changed, decisions, new open questions, next action).

`CLAUDE.md` (this file) = architecture truth. `PROJECT_STATE.md` = where we are now. Keep both current.

---

## 1. What we are building (plain English)

**DrivePulse** is a usage-based auto-insurance (UBI) **data mesh** on Azure Databricks.

The business it models: an insurer prices car-insurance premiums based on *how people
actually drive*, not just their age and ZIP code. Sensors in the car (speed, braking,
GPS, accelerometer) stream in continuously. The insurer combines that driving behavior
with policy records, claims history, vehicle reference data, crash statistics, and
weather to do three things:

1. **Price risk** — a safe driver pays less; a risky one pays more (the "risk score").
2. **Handle claims** — when a crash happens, reconstruct what the car was doing at the
   moment of loss (huge for settling claims fast and catching fraud).
3. **Coach drivers / manage fleets** — weekly feedback, predictive maintenance, recall alerts.

On top of the data, we build **GenAI agents** that automate the analyst workflows
(claims intake, underwriting quotes, fleet Q&A). The data platform is the foundation
the agents stand on — agents only ever read from the **gold** layer.

**Why a mesh, not one lake:** three real teams own three real data products. They
publish gold tables and consume each other's gold tables by name — no copying, no
reaching into each other's raw data. That separation *is* the mesh.

---

## 2. The mesh: three Unity Catalog domains

Exactly **three** catalogs. Each is owned by one team, each holds one domain end-to-end.

| Catalog            | Owning team                | Domain responsibility                                   |
|--------------------|----------------------------|---------------------------------------------------------|
| `prod_telematics`  | Connected Vehicle / IoT    | Trips, telemetry events, driver behavior, hard-events   |
| `prod_policy`      | Underwriting               | Policies, drivers, vehicles-on-policy, coverages, vehicle reference |
| `prod_claims`      | Claims Operations          | Claims, FNOL, status history, payments, adjuster notes  |

Logical sub-domains roll up under the owning team's catalog (don't create extra catalogs):

- **Vehicle reference** (NHTSA vPIC, recalls) → lives in `prod_policy` (underwriting owns
  "what is this vehicle?"), or is **federated** from external Postgres — never ingested.
- **Crash & safety** (FARS, ODI complaints) → federated reference, or sits in `prod_claims`
  for fraud / loss research.
- **Environment** (weather, OSM, traffic) → **always federated**, never a catalog of its own.
- **Documents / RAG** → split by ownership: policy forms in `prod_policy.docs`,
  claim narratives in `prod_claims.docs`, vehicle manuals/recall letters in `prod_telematics.docs`.

### Schema layout (identical medallion inside every catalog)

```
<catalog>.bronze.*    raw, append-only, as-ingested (schema-on-read where needed)
<catalog>.silver.*    cleaned, conformed, deduplicated, SCD2 dims, CDC applied
<catalog>.gold.*      Kimball star schemas + cross-domain marts (what agents query)
<catalog>.docs.*      chunked text + embeddings for Vector Search / RAG
```

### Cross-domain consumption (the mesh rule)

Always use three-part names. **Never copy another domain's data.** A consumer joins the
*producer's published gold table*:

```sql
SELECT t.driver_key, t.trip_risk, p.premium, c.claim_amount
FROM   prod_telematics.gold.fact_trip          t
JOIN   prod_policy.gold.dim_policy             p ON t.policy_key = p.policy_key
LEFT   JOIN prod_claims.gold.fact_claim        c ON c.trip_key   = t.trip_key;
```

A cross-domain mart lives in the catalog of the team that *consumes it of record*
(e.g. `mart_claim_360` → `prod_claims.gold` because Claims owns that question).

---

## 3. Pattern coverage map (every pattern must appear at least once)

| Pattern                         | Where it lands                                                                 |
|---------------------------------|--------------------------------------------------------------------------------|
| **Auto Loader** (`cloudFiles`)  | Batch landings: policies (CSV), claims (CSV), recalls (JSON), vehicle ref      |
| **Event Hubs + Structured Streaming** | Telemetry: replay VED at 10–100× into Event Hubs → streaming bronze       |
| **Lakehouse Federation**        | Weather (Postgres), vPIC (Postgres/SQL Server), OSM (PostGIS) — query in place |
| **Lakeflow Declarative Pipelines** (ex-DLT) | Silver pipelines: expectations, quarantine, materialized gold      |
| **SCD2**                        | `dim_driver`, `dim_vehicle`, `dim_policy`, `dim_coverage` via `APPLY CHANGES INTO` |
| **CDC**                         | Claim status (FNOL→investigating→settled→closed), policy endorsements          |
| **Unity Catalog governance**    | Row filters (per-insurer tenancy), column masks (PII), tags, lineage           |
| **Vector Search + RAG**         | `*.docs` schemas — policy forms, recall letters, complaint narratives          |
| **Mosaic AI Agent Framework**   | Agents in `/agents`, served as Model Serving endpoints, evaluated with MLflow  |

If you implement a feature and it doesn't exercise one of these, ask whether it belongs.

---

## 4. Gold layer = Kimball stars per domain

**Conformed dimensions** (SCD2, shared across the mesh):
`dim_driver`, `dim_vehicle`, `dim_policy`, `dim_coverage`, `dim_date`, `dim_time`,
`dim_location` (H3-indexed), `dim_weather_condition`, `dim_recall_campaign`.

**Facts by domain:**

| Domain      | Fact table                        | Grain                          |
|-------------|-----------------------------------|--------------------------------|
| Telematics  | `fact_trip`                       | one row per trip               |
|             | `fact_telemetry_event`            | one row per hard-event         |
|             | `fact_trip_summary_daily`         | one row per driver-day         |
| Policy      | `fact_policy_inforce_monthly`     | one row per policy-month       |
|             | `fact_policy_transaction`         | one row per new/renew/cancel/endorse |
| Claims      | `fact_claim`                      | one row per claim              |
|             | `fact_claim_status_history`       | one row per status change      |
|             | `fact_claim_payment`              | one row per payment            |

**Cross-domain marts** (the analytics payoff — what agents actually query):
`mart_driver_risk_score`, `mart_claim_360`, `mart_pricing_recommendation`,
`mart_recall_impact`, `mart_geo_risk_heatmap`, `mart_fleet_health`.

---

## 5. Datasets (all public; verified downloadable). See `docs/datasets.md` for links.

| Domain      | Sources                                                                       |
|-------------|-------------------------------------------------------------------------------|
| Telematics  | Vehicle Energy Dataset (VED) + Extended VED (eVED), UAH-DriveSet, comma2k19    |
| Policy      | Porto Seguro Safe Driver (~595K train rows), Kaggle vehicle-insurance sets     |
| Claims      | Allstate Claims Severity (~188K), Allstate Claim Prediction Challenge          |
| Vehicle     | NHTSA vPIC (Postgres/SQL Server DBs), NHTSA Recalls API (30K+ recalls)          |
| Safety      | NHTSA FARS (~989K fatalities since 1975), ODI complaint narratives             |
| Environment | NOAA GHCN-Daily weather, OpenStreetMap (PostGIS), FHWA HPMS AADT               |
| Documents   | NHTSA recall letters (PDF), state DOI sample policy forms, VOQ narratives      |

**Honest gaps & approved fixes (document these in the repo README):**
- No public dataset links telematics→policy→claim. **Fix:** deterministic synthetic join
  keys (Faker + fixed seed) so VED vehicles map to Porto Seguro policies map to Allstate
  claims. Label this clearly as "real public data, synthetically linked."
- No live vehicle stream exists publicly. **Fix:** replay VED chronologically into Event
  Hubs at 50–100× speed. This is the standard demo pattern — say so in the README.
- Volume target: **≥ 50K** records minimum everywhere; telemetry replayed to billions of
  stream events to prove large-scale processing (partitioning, Z-order, liquid clustering).

---

## 6. GenAI agentic destination (build after gold is solid)

Each agent reads **only** from gold/docs, is served as a Model Serving endpoint, and ships
with an **MLflow Agent Evaluation** harness (this is what makes it architect-grade, not a toy).

1. **Claims FNOL Copilot** — crash signal → pulls policy + vehicle + weather-at-loss +
   prior claims + similar trip telemetry → drafts the First Notice of Loss with citations.
2. **Underwriting Copilot** — new quote → telematics history + driver record + recalls/safety
   + geo-risk → explainable premium citing the actual policy-form PDF.
3. **Fleet Ops Genie** — natural-language Q&A across the whole mesh ("riskiest 10 VINs this
   month with open recalls and recommended actions").

---

## 7. Conventions (follow exactly)

- **Language:** PySpark + Spark SQL. Python 3.11. Notebooks as `.py` (Databricks source
  format with `# COMMAND ----------` cells) so they diff cleanly in git.
- **Naming:** snake_case everywhere. Facts `fact_*`, dims `dim_*`, marts `mart_*`,
  bronze raw tables `raw_*` or source-named, quarantine `*_quarantine`.
- **Catalogs are environment-prefixed via bundle variables**, not hardcoded. Use the
  `${var.catalog_telematics}` style substitution so `dev` and `prod` targets differ.
- **No secrets in code.** Read from Databricks secret scopes / `.env` (see `.env.example`).
  Event Hubs connection strings, storage keys, PATs → secret scope only.
- **Idempotent + restartable.** Streaming uses checkpoints; batch uses MERGE, never blind INSERT.
- **Every silver table** has Lakeflow expectations (GPS sanity, speed/accel bounds, timestamp
  monotonicity, schema, PII-presence). Failed rows → `*_quarantine`, never dropped silently.
- **Tests** live in `/tests`; transformations are pure functions where possible so they're unit-testable off-cluster.
- **One ADR per significant decision** in `docs/adr/` (start from `0001`).

---

## 8. Repo structure

```
drivepulse-lakehouse/
├── CLAUDE.md                  ← you are here
├── README.md                  ← public-facing overview + architecture diagram
├── FIRST_TASK.md              ← the first prompt to run me with
├── databricks.yml             ← bundle root (Declarative Automation Bundle)
├── .env.example               ← copy to .env; never commit .env
├── requirements.txt
├── .github/workflows/         ← CI (validate + test) and CD (deploy bundle)
├── resources/                 ← bundle resource defs: catalogs, schemas, jobs, pipelines
├── domains/
│   ├── telematics/{bronze,silver,gold,docs}/   → prod_telematics
│   ├── policy/{bronze,silver,gold,docs}/        → prod_policy
│   └── claims/{bronze,silver,gold,docs}/        → prod_claims
├── ingestion/
│   ├── seed_data/             ← scripts to download the public datasets
│   └── eventhubs_simulator/   ← VED telemetry replay → Event Hubs
├── agents/                    ← Mosaic AI agents + eval harnesses
├── src/drivepulse/common/     ← shared utils: schemas, config, logging, H3, SCD2 helpers
├── docs/                      ← architecture.md, datasets.md, adr/
└── tests/
```

---

## 9. How to deploy (Declarative Automation Bundle)

```bash
databricks bundle validate                 # check config
databricks bundle deploy  -t dev           # deploy to dev target
databricks bundle run     bootstrap_uc -t dev   # run a named job/pipeline
databricks bundle deploy  -t prod          # promote
```

Targets and the workspace host come from `databricks.yml`; auth comes from the matching
profile in `~/.databrickscfg` (see SETUP in README). Never put host/token in code.

---

## 10. Build order (do not skip ahead)

1. **Bootstrap UC** — create the 3 catalogs + medallion schemas (via bundle `resources/`).
2. **Telematics vertical slice first** — VED → Event Hubs replay → streaming bronze →
   Lakeflow silver (trip sessionization) → gold `fact_trip` + `dim_driver`. One domain,
   end to end, proven, before touching the others.
3. **Policy + Claims bronze/silver/gold** following the same template.
4. **Federation** sources wired in (weather/vPIC/OSM).
5. **UC governance** — row filters + column masks + PII tags.
6. **`docs` + Vector Search** indexes.
7. **Agents** + MLflow eval, one at a time, starting with Claims FNOL Copilot.

---

## 11. Do / Don't

**Do**
- Ask before creating a 4th catalog, renaming a catalog, or deleting any table.
- Keep cross-domain access read-only via three-part names.
- Write a short ADR when you make an architecture choice.
- Prefer `MERGE` / `APPLY CHANGES INTO` over drop-and-recreate.

**Don't**
- Don't hardcode catalog names, hosts, tokens, or connection strings.
- Don't ingest federated sources (weather/vPIC/OSM stay external).
- Don't let agents read silver or bronze — gold/docs only.
- Don't drop failed rows silently — quarantine them.
- Don't commit `.env`, data files, or `~/.databrickscfg`.

---

## 12. Environment facts

- **Cloud:** Azure. Resource group `rg_mission_2026_dataai`, region **East US**.
- **Storage:** ADLS Gen2 (Unity Catalog external locations / managed storage).
- **Streaming:** Azure Event Hubs (Kafka-compatible endpoint).
- **Workspace URL form:** `https://adb-<id>.<n>.azuredatabricks.net`.
- This is a **free/trial-tier** workspace — keep clusters small, autoterminate aggressively,
  and prefer serverless or single-node where possible.
