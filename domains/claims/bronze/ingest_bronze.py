# Databricks notebook source
# MAGIC %md
# MAGIC # Claims Bronze — dynamic Auto Loader ingestion
# MAGIC
# MAGIC One reusable, config-driven notebook that lands **all** claims source files from the ADLS
# MAGIC landing volume into `prod_claims.bronze.raw_*` tables.
# MAGIC
# MAGIC - **Auto Loader** (`cloudFiles`), append-only, **string-safe** (no type inference — keep source as text).
# MAGIC - Rescued/unexpected data captured in `_rescued_data`.
# MAGIC - Ingest metadata on every row: `_ingest_ts`, `_source_file`, `_batch_id`, `_rescued_data`.
# MAGIC - **Idempotent + checkpointed** (`trigger(availableNow=True)`): re-runs add 0 rows (US-B3).
# MAGIC - PII columns **tagged** in Unity Catalog (no masking) per the bronze contract.
# MAGIC - Sources whose file is not yet in the landing zone are **skipped** (e.g. NHTSA complaints until uploaded).

# COMMAND ----------
# DBTITLE 1,Parameters
dbutils.widgets.text("catalog", "prod_claims", "Target catalog")
dbutils.widgets.text("landing_volume", "/Volumes/prod_claims/bronze/claims_landing_zone", "Landing volume (ADLS-backed)")
dbutils.widgets.text("checkpoint_volume", "/Volumes/prod_claims/bronze/checkpoints", "Checkpoint volume")

CATALOG = dbutils.widgets.get("catalog")
SCHEMA = "bronze"
LANDING = dbutils.widgets.get("landing_volume").rstrip("/")
CHECKPOINT = dbutils.widgets.get("checkpoint_volume").rstrip("/")

# COMMAND ----------
# DBTITLE 1,Source registry (one entry per source file)
# Add the complaints entry's file to the landing zone and re-run to load the 5th table.
SOURCES = [
    {"table": "raw_insurance_claims", "file": "insurance_claims.csv", "sep": ",",  "header": True,
     "pii": ["policy_number", "insured_zip", "incident_location"]},
    {"table": "raw_carclaims",        "file": "carclaims.csv",        "sep": ",",  "header": True,
     "pii": ["PolicyNumber"]},
    {"table": "raw_claims_by_type",   "file": "sample_type_claim.csv","sep": ";",  "header": True,
     "pii": ["ID"]},
    {"table": "raw_claim_severity",   "file": "freMTPL2sev.csv",      "sep": ",",  "header": True,
     "pii": ["IDpol"]},
    {"table": "raw_complaints",       "file": "FLAT_CMPL.txt",        "sep": "\t", "header": False,
     "pii": ["VIN", "CITY", "STATE"]},
]

# COMMAND ----------
# DBTITLE 1,Imports + run id
import json
import uuid
from pyspark.sql import functions as F

BATCH_ID = str(uuid.uuid4())
print(f"catalog={CATALOG} landing={LANDING} checkpoint={CHECKPOINT}")
print(f"batch_id={BATCH_ID}")

# COMMAND ----------
# DBTITLE 1,Discover files actually present in the landing zone
present = {f.name for f in dbutils.fs.ls(LANDING)}
print("Files in landing zone:", sorted(present))

# COMMAND ----------
# DBTITLE 1,Reusable Auto Loader ingest function
def ingest(src):
    """Stream one source file -> prod_claims.bronze.<table> via Auto Loader (append-only)."""
    table = src["table"]
    fqn = f"{CATALOG}.{SCHEMA}.{table}"
    chk = f"{CHECKPOINT}/{table}"

    stream = (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("cloudFiles.inferColumnTypes", "false")          # string-safe: keep source types as text
        .option("cloudFiles.schemaLocation", f"{chk}/_schema")
        .option("cloudFiles.schemaEvolutionMode", "rescue")
        .option("rescuedDataColumn", "_rescued_data")
        .option("header", str(src["header"]).lower())
        .option("sep", src["sep"])
        .option("pathGlobFilter", src["file"])                   # pick only this source's file
        .load(LANDING)
        .withColumn("_ingest_ts", F.current_timestamp())
        .withColumn("_source_file", F.col("_metadata.file_path"))
        .withColumn("_batch_id", F.lit(BATCH_ID))
    )

    query = (
        stream.writeStream
        .option("checkpointLocation", chk)
        .option("mergeSchema", "true")
        .trigger(availableNow=True)
        .toTable(fqn)
    )
    query.awaitTermination()
    return fqn

# COMMAND ----------
# DBTITLE 1,Ensure checkpoint volume exists
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.checkpoints")

# COMMAND ----------
# DBTITLE 1,Load every present source
results = {}
for src in SOURCES:
    table = src["table"]
    if src["file"] not in present:
        results[table] = {"status": "SKIPPED_no_file", "file": src["file"], "rows": None}
        print(f"SKIP  {table}: '{src['file']}' not in landing zone")
        continue
    fqn = ingest(src)
    rows = spark.table(fqn).count()
    results[table] = {"status": "OK", "file": src["file"], "rows": rows, "fqn": fqn}
    print(f"OK    {fqn}: {rows} rows")

# COMMAND ----------
# DBTITLE 1,Tag PII columns (no masking)
for src in SOURCES:
    table = src["table"]
    if results.get(table, {}).get("status") != "OK":
        continue
    fqn = f"{CATALOG}.{SCHEMA}.{table}"
    existing = {c.lower(): c for c in spark.table(fqn).columns}
    for pii in src["pii"]:
        if pii.lower() in existing:
            real = existing[pii.lower()]
            spark.sql(f"ALTER TABLE {fqn} ALTER COLUMN `{real}` SET TAGS ('pii' = 'true')")
            print(f"tagged PII  {fqn}.{real}")
        else:
            print(f"WARN PII column not found (skipped): {fqn}.{pii}")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Validation lives in the shared notebook
# MAGIC Row-count validation is now a reusable, cross-domain asset:
# MAGIC **`validation/dynamic_row_count_validation.py`**. Run it with `expectations`, e.g.
# MAGIC `{"prod_claims.bronze.raw_insurance_claims": 1000, ...}`. This notebook only *loads*;
# MAGIC the validator *checks*. (Counts are still returned below for the caller.)

# COMMAND ----------
# DBTITLE 1,Return results to the caller
dbutils.notebook.exit(json.dumps(results, indent=2))
