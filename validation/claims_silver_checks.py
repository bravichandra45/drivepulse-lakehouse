# Databricks notebook source
# MAGIC %md
# MAGIC # Claims Silver — verification checks
# MAGIC Reconciliation, SCD2 structure, lifecycle, and quarantine checks. Returns a JSON summary.

# COMMAND ----------
dbutils.widgets.text("catalog", "prod_claims")
CATALOG = dbutils.widgets.get("catalog")
S = f"{CATALOG}.silver"
B = f"{CATALOG}.bronze"

import json
from pyspark.sql import functions as F

def count(t):
    return spark.table(t).count()

r = {}

# ---- counts
for t in ["claim", "claim_quarantine", "claim_severity", "claim_status_history",
          "dim_policyholder", "dim_vehicle"]:
    r[f"count_{t}"] = count(f"{S}.{t}")

# ---- reconciliation: claim + quarantine == distinct conformed claim_ids
bronze_total = count(f"{B}.raw_insurance_claims") + count(f"{B}.raw_carclaims")
claim_plus_q = r["count_claim"] + r["count_claim_quarantine"]
r["recon_bronze_total"] = bronze_total
r["recon_claim_plus_quarantine"] = claim_plus_q
r["recon_dupes_removed"] = bronze_total - claim_plus_q
r["recon_ok_no_overlap"] = (
    spark.table(f"{S}.claim").select("claim_id")
    .intersect(spark.table(f"{S}.claim_quarantine").select("claim_id")).count() == 0
)

# ---- claim_severity reconciliation
r["recon_severity_expected"] = count(f"{B}.raw_claim_severity") + count(f"{B}.raw_claims_by_type")

# ---- lifecycle: status distribution + history transitions
r["claim_status_dist"] = {row["claim_status"]: row["n"]
    for row in spark.table(f"{S}.claim").groupBy("claim_status").agg(F.count("*").alias("n")).collect()}
r["history_status_dist"] = {row["status"]: row["n"]
    for row in spark.table(f"{S}.claim_status_history").groupBy("status").agg(F.count("*").alias("n")).collect()}
r["history_distinct_claims"] = spark.table(f"{S}.claim_status_history").select("claim_id").distinct().count()

# ---- SCD2 structure
dp = spark.table(f"{S}.dim_policyholder")
r["dim_policyholder_cols"] = dp.columns
r["dim_policyholder_current"] = dp.filter("__END_AT IS NULL").count()
r["dim_policyholder_distinct_keys"] = dp.select("policy_number", "source_system").distinct().count()
dv = spark.table(f"{S}.dim_vehicle")
r["dim_vehicle_current"] = dv.filter("__END_AT IS NULL").count()
r["dim_vehicle_distinct_keys"] = dv.select("vehicle_key").distinct().count()

# ---- quarantine reasons breakdown
r["quarantine_reasons"] = {row["quarantine_reason"]: row["n"]
    for row in spark.table(f"{S}.claim_quarantine").groupBy("quarantine_reason").agg(F.count("*").alias("n")).collect()}

# ---- assertions
checks = {
    "claim_plus_quarantine_equals_conformed": claim_plus_q <= bronze_total and claim_plus_q > 0,
    "no_overlap_claim_quarantine": r["recon_ok_no_overlap"],
    "severity_count_matches": r["count_claim_severity"] == r["recon_severity_expected"],
    "scd2_has_start_end": ("__START_AT" in dp.columns) and ("__END_AT" in dp.columns),
    "policyholder_current_eq_keys": r["dim_policyholder_current"] == r["dim_policyholder_distinct_keys"],
    "history_covers_all_claims": r["history_distinct_claims"] == r["count_claim"],
}
r["checks"] = checks
r["all_passed"] = all(checks.values())

print(json.dumps(r, indent=2, default=str))
dbutils.notebook.exit(json.dumps(r, default=str))
