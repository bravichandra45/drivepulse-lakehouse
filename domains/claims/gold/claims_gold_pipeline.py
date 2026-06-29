# Databricks notebook source
# MAGIC %md
# MAGIC # Claims Gold — Lakeflow Declarative Pipeline (Kimball star + marts)
# MAGIC Reads `prod_claims.silver`, materializes the gold star and marts.
# MAGIC
# MAGIC - **Dims:** dim_date, dim_claim_status, dim_claim_type, dim_geography, dim_incident,
# MAGIC   dim_policyholder (current SCD2), dim_vehicle (current SCD2).
# MAGIC - **Facts:** fact_claim (one per claim), fact_claim_lifecycle (accumulating snapshot),
# MAGIC   fact_claim_status_history (one per status change).
# MAGIC - **Marts:** mart_claims_kpi (US-G1), mart_fraud_signals (US-G2), feature_fraud (US-G3).
# MAGIC
# MAGIC Loss ratio & claim frequency need policy exposure (cross-domain) — left null until UC Policy lands.

# COMMAND ----------
import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType

CATALOG = spark.conf.get("catalog", "prod_claims")
SILVER = f"{CATALOG}.silver"
AMT = DecimalType(14, 2)

def _sk(*cols):
    """Stable surrogate key from natural-key columns."""
    return F.sha2(F.concat_ws("|", *[F.coalesce(c.cast("string"), F.lit("∅")) for c in cols]), 256)

# ---------------------------------------------------------------- dims
@dlt.table(name="dim_date", comment="Date dimension spanning claim incident/fnol/settlement dates.")
def dim_date():
    c = spark.read.table(f"{SILVER}.claim")
    b = c.select(
        F.min(F.least("incident_date", "fnol_date")).alias("mn"),
        F.max(F.greatest("settlement_date", "fnol_date", "incident_date")).alias("mx"),
    ).collect()[0]
    mn, mx = b["mn"], b["mx"]
    d = (spark.createDataFrame([(mn, mx)], "mn date, mx date")
         .select(F.explode(F.sequence(F.col("mn"), F.col("mx"), F.expr("interval 1 day"))).alias("date")))
    return d.select(
        (F.year("date") * 10000 + F.month("date") * 100 + F.dayofmonth("date")).alias("date_key"),
        F.col("date"),
        F.year("date").alias("year"), F.month("date").alias("month"),
        F.dayofmonth("date").alias("day"), F.quarter("date").alias("quarter"),
        F.date_format("date", "EEEE").alias("day_of_week"),
        (F.dayofweek("date").isin(1, 7)).alias("is_weekend"),
    )

@dlt.table(name="dim_claim_status", comment="Claim status dimension.")
def dim_claim_status():
    c = spark.read.table(f"{SILVER}.claim").select("claim_status").distinct().where("claim_status IS NOT NULL")
    return c.select(_sk(F.col("claim_status")).alias("status_key"),
                    F.col("claim_status").alias("claim_status"),
                    F.col("claim_status").isin("denied", "closed", "settled").alias("is_terminal"))

@dlt.table(name="dim_claim_type", comment="Claim/incident type dimension.")
def dim_claim_type():
    c = spark.read.table(f"{SILVER}.claim").select("claim_type").distinct().where("claim_type IS NOT NULL")
    return c.select(_sk(F.col("claim_type")).alias("claim_type_key"), F.col("claim_type"))

@dlt.table(name="dim_geography", comment="Geography dimension (incident location).")
def dim_geography():
    c = spark.read.table(f"{SILVER}.claim").select("incident_location").distinct().where("incident_location IS NOT NULL")
    return c.select(_sk(F.col("incident_location")).alias("geography_key"), F.col("incident_location"))

@dlt.table(name="dim_incident", comment="Incident dimension (severity x claim_type).")
def dim_incident():
    c = spark.read.table(f"{SILVER}.claim").select("severity", "claim_type").distinct()
    return c.select(_sk(F.col("severity"), F.col("claim_type")).alias("incident_key"),
                    F.col("severity"), F.col("claim_type"))

@dlt.table(name="dim_policyholder", comment="Current policyholder (from silver SCD2).")
def dim_policyholder():
    return spark.read.table(f"{SILVER}.dim_policyholder").where("__END_AT IS NULL")

@dlt.table(name="dim_vehicle", comment="Current vehicle (from silver SCD2).")
def dim_vehicle():
    return spark.read.table(f"{SILVER}.dim_vehicle").where("__END_AT IS NULL")

# ---------------------------------------------------------------- facts
@dlt.table(name="fact_claim", comment="One row per claim: dim keys + measures (+ key descriptive attrs).")
def fact_claim():
    c = spark.read.table(f"{SILVER}.claim")
    vkey = _sk(F.col("auto_make"), F.col("auto_model"), F.col("auto_year"), F.col("vehicle_category"))
    return c.select(
        F.col("claim_id"), F.col("source_system"), F.col("policy_number"),
        (F.year("incident_date") * 10000 + F.month("incident_date") * 100 + F.dayofmonth("incident_date")).alias("date_key"),
        _sk(F.col("claim_status")).alias("status_key"),
        _sk(F.col("claim_type")).alias("claim_type_key"),
        _sk(F.col("incident_location")).alias("geography_key"),
        _sk(F.col("severity"), F.col("claim_type")).alias("incident_key"),
        vkey.alias("vehicle_key"),
        # descriptive (denormalized for self-contained marts)
        F.col("auto_make"), F.col("severity"), F.col("claim_type"), F.col("incident_location"),
        F.col("policyholder_age"), F.col("policyholder_sex"), F.col("fault"), F.col("vehicle_category"),
        F.col("claim_status"),
        # measures
        F.col("total_claim_amount"), F.col("injury_claim"), F.col("property_claim"), F.col("vehicle_claim"),
        F.col("fraud").cast("int").alias("is_fraud"), F.lit(1).alias("claim_count"),
    )

@dlt.table(name="fact_claim_lifecycle", comment="Accumulating snapshot: milestone dates + stage lags + cycle time.")
def fact_claim_lifecycle():
    c = spark.read.table(f"{SILVER}.claim")
    return c.select(
        F.col("claim_id"), F.col("source_system"),
        F.col("incident_date"), F.col("fnol_date"), F.col("settlement_date"),
        F.col("claim_status"),
        F.datediff("fnol_date", "incident_date").alias("days_incident_to_fnol"),
        F.datediff("settlement_date", "fnol_date").alias("days_fnol_to_settlement"),
        F.col("cycle_time_days"),
        F.col("settlement_date").isNotNull().alias("is_closed"),
    )

@dlt.table(name="fact_claim_status_history", comment="One row per status change (from silver).")
def fact_claim_status_history():
    h = spark.read.table(f"{SILVER}.claim_status_history")
    return h.select("claim_id", "source_system",
                    _sk(F.col("status")).alias("status_key"),
                    F.col("status"), F.col("status_date"), F.col("seq"))

# ---------------------------------------------------------------- marts
@dlt.table(name="mart_claims_kpi", comment="US-G1 KPI mart by source_system. Reconciles to fact_claim.")
def mart_claims_kpi():
    fc = dlt.read("fact_claim")
    fl = dlt.read("fact_claim_lifecycle").select("claim_id", "is_closed", "cycle_time_days")
    j = fc.join(fl, "claim_id", "left")
    g = j.groupBy("source_system").agg(
        F.count("*").alias("claim_count"),
        F.sum("is_fraud").alias("fraud_count"),
        F.sum("total_claim_amount").alias("total_incurred"),
        F.avg("total_claim_amount").cast(AMT).alias("avg_severity"),
        F.sum(F.when(F.col("claim_status") == "denied", 1).otherwise(0)).alias("denied_count"),
        F.sum(F.when(F.col("is_closed"), 1).otherwise(0)).alias("closed_count"),
        F.sum(F.when(~F.col("is_closed"), 1).otherwise(0)).alias("open_count"),
        F.avg("cycle_time_days").alias("avg_cycle_time_days"),
    )
    return g.select(
        "source_system", "claim_count", "fraud_count",
        (F.col("fraud_count") / F.col("claim_count")).alias("fraud_rate"),
        "total_incurred", "avg_severity",
        (F.col("denied_count") / F.col("claim_count")).alias("denial_rate"),
        "open_count", "closed_count", "avg_cycle_time_days",
        F.lit(None).cast("double").alias("loss_ratio"),       # needs premium (policy domain)
        F.lit(None).cast("double").alias("claim_frequency"),  # needs exposure (policy domain)
    )

@dlt.table(name="mart_fraud_signals", comment="US-G2 fraud rate by make / severity / claim_type.")
def mart_fraud_signals():
    fc = dlt.read("fact_claim")
    def sig(dim, label):
        return (fc.groupBy(F.col(dim).alias("dimension_value"))
                  .agg(F.count("*").alias("claim_count"), F.sum("is_fraud").alias("fraud_count"))
                  .withColumn("signal_dimension", F.lit(label))
                  .withColumn("fraud_rate", F.col("fraud_count") / F.col("claim_count")))
    return (sig("auto_make", "make")
            .unionByName(sig("severity", "severity"))
            .unionByName(sig("claim_type", "claim_type"))
            .select("signal_dimension", "dimension_value", "claim_count", "fraud_count", "fraud_rate"))

@dlt.table(name="feature_fraud", comment="US-G3 ML feature table: one row per claim, no outcome leakage.")
def feature_fraud():
    fc = dlt.read("fact_claim")
    # Exclude leakage: claim_status, settlement/fnol/cycle (post-outcome). Keep pre-decision features + label.
    return fc.select(
        "claim_id", "source_system",
        "policyholder_age", "policyholder_sex", "auto_make", "vehicle_category",
        "severity", "claim_type", "incident_location", "fault",
        "total_claim_amount", "injury_claim", "property_claim", "vehicle_claim",
        F.col("is_fraud").alias("label"),
    )
