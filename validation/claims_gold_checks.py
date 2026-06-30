# Databricks notebook source
# MAGIC %md # Claims Gold — verification checks (star reconciliation, RI, no-leakage)

# COMMAND ----------
dbutils.widgets.text("catalog", "prod_claims")
CATALOG = dbutils.widgets.get("catalog")
G, S = f"{CATALOG}.gold", f"{CATALOG}.silver"

import json
from pyspark.sql import functions as F

def cnt(t): return spark.table(t).count()
r = {}

for t in ["dim_date","dim_claim_status","dim_claim_type","dim_geography","dim_incident",
          "dim_policyholder","dim_vehicle","fact_claim","fact_claim_lifecycle",
          "fact_claim_status_history","mart_claims_kpi","mart_fraud_signals","feature_fraud"]:
    r[f"count_{t}"] = cnt(f"{G}.{t}")

silver_claim = cnt(f"{S}.claim")
r["silver_claim"] = silver_claim

# referential integrity: every fact_claim dim key exists in its dim
fc = spark.table(f"{G}.fact_claim")
def orphans(keycol, dim, dimkey, filt=None):
    left = fc.select(keycol).where(f"{keycol} IS NOT NULL")
    if filt: left = left.where(filt)
    return left.join(spark.table(f"{G}.{dim}").select(F.col(dimkey).alias(keycol)), keycol, "left_anti").count()
ri = {
    "status_key": orphans("status_key", "dim_claim_status", "status_key"),
    "claim_type_key": orphans("claim_type_key", "dim_claim_type", "claim_type_key", "claim_type IS NOT NULL"),
    "geography_key": orphans("geography_key", "dim_geography", "geography_key", "incident_location IS NOT NULL"),
    "incident_key": orphans("incident_key", "dim_incident", "incident_key"),
}
r["ri_orphans"] = ri

# mart reconciliation
kpi = spark.table(f"{G}.mart_claims_kpi")
r["kpi_sum_claim_count"] = kpi.agg(F.sum("claim_count")).collect()[0][0]
r["kpi_sum_fraud_count"] = kpi.agg(F.sum("fraud_count")).collect()[0][0]
r["factclaim_fraud_sum"] = fc.agg(F.sum("is_fraud")).collect()[0][0]
r["kpi_rows"] = [row.asDict() for row in kpi.select("source_system","claim_count","fraud_count","fraud_rate","denial_rate","open_count","closed_count","loss_ratio").collect()]
r["fraud_signal_dims"] = sorted([x["signal_dimension"] for x in spark.table(f"{G}.mart_fraud_signals").select("signal_dimension").distinct().collect()])

# feature_fraud: no leakage columns
leak = {"claim_status","settlement_date","fnol_date","cycle_time_days","is_closed"}
ff_cols = set(spark.table(f"{G}.feature_fraud").columns)
r["feature_fraud_cols"] = sorted(ff_cols)
r["feature_fraud_has_label"] = "label" in ff_cols
r["feature_fraud_no_leakage"] = len(leak & ff_cols) == 0

checks = {
    "fact_claim_eq_silver": r["count_fact_claim"] == silver_claim,
    "lifecycle_eq_silver": r["count_fact_claim_lifecycle"] == silver_claim,
    "status_history_eq_silver": r["count_fact_claim_status_history"] == cnt(f"{S}.claim_status_history"),
    "feature_fraud_eq_silver": r["count_feature_fraud"] == silver_claim,
    "ri_all_zero": all(v == 0 for v in ri.values()),
    "kpi_reconciles": r["kpi_sum_claim_count"] == r["count_fact_claim"] and r["kpi_sum_fraud_count"] == r["factclaim_fraud_sum"],
    "fraud_signals_present": set(r["fraud_signal_dims"]) >= {"make","severity","claim_type"},
    "feature_no_leakage": r["feature_fraud_no_leakage"] and r["feature_fraud_has_label"],
}
r["checks"] = checks
r["all_passed"] = all(checks.values())
print(json.dumps(r, indent=2, default=str))

flat = {
    "all_passed": r["all_passed"],
    "count_fact_claim": r["count_fact_claim"],
    "count_fact_claim_lifecycle": r["count_fact_claim_lifecycle"],
    "count_fact_claim_status_history": r["count_fact_claim_status_history"],
    "count_feature_fraud": r["count_feature_fraud"],
    "count_mart_claims_kpi": r["count_mart_claims_kpi"],
    "count_mart_fraud_signals": r["count_mart_fraud_signals"],
    "count_dim_date": r["count_dim_date"],
    "count_dim_vehicle": r["count_dim_vehicle"],
    "count_dim_policyholder": r["count_dim_policyholder"],
    "silver_claim": r["silver_claim"],
    "kpi_sum_claim_count": r["kpi_sum_claim_count"],
    "kpi_sum_fraud_count": r["kpi_sum_fraud_count"],
    "factclaim_fraud_sum": r["factclaim_fraud_sum"],
    "ri_orphans_total": sum(ri.values()),
    "fraud_signal_dims": ",".join(r["fraud_signal_dims"]),
    "feature_no_leakage": r["feature_fraud_no_leakage"],
}
for k, v in checks.items():
    flat[f"check_{k}"] = v
dbutils.notebook.exit(json.dumps(flat, default=str))
