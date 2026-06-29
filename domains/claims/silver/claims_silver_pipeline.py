# Databricks notebook source
# MAGIC %md
# MAGIC # Claims Silver — Lakeflow Declarative Pipeline
# MAGIC Conforms Bronze `raw_*` into cleaned/typed/deduped Silver, with expectations + quarantine,
# MAGIC a seeded (synthetic) claim lifecycle + status-history (CDC), and SCD2 dims (APPLY CHANGES).
# MAGIC
# MAGIC - **S1** `silver.claim` — conform insurance_claims + carclaims into one claim grain.
# MAGIC - **S2** `silver.claim_status_history` — derived lifecycle, one row per transition.
# MAGIC - **S3** `silver.claim_quarantine` — rows failing expectations (nothing dropped).
# MAGIC - **S4** `silver.dim_policyholder`, `silver.dim_vehicle` — SCD2 via APPLY CHANGES.
# MAGIC - Plus `silver.claim_severity` (freMTPL2sev + Spanish by-type).
# MAGIC
# MAGIC Lifecycle fields (fnol_date/claim_status/settlement_date/cycle_time_days) are **synthetic,
# MAGIC deterministic** (seeded by a hash of claim_id) — documented per ADR 0002.

# COMMAND ----------
import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType

CATALOG = spark.conf.get("catalog", "prod_claims")
BRONZE = f"{CATALOG}.bronze"
AMT = DecimalType(14, 2)

def _to_date_multi(c):
    return F.coalesce(
        F.to_date(c, "yyyy-MM-dd"), F.to_date(c, "MM/dd/yyyy"),
        F.to_date(c, "dd-MM-yyyy"), F.to_date(c, "d-M-yyyy"),
    )

_MONTHS = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
           "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}

def _month_num(c):
    e = F.lit(None).cast("int")
    lc = F.lower(F.substring(F.trim(c), 1, 3))
    for k, v in _MONTHS.items():
        e = F.when(lc == k, F.lit(v)).otherwise(e)
    return e

# ---------------------------------------------------------------- S1: conform
def _insurance():
    df = spark.read.table(f"{BRONZE}.raw_insurance_claims")
    return df.select(
        F.lit("insurance_claims").alias("source_system"),
        F.col("policy_number").cast("string").alias("policy_number"),
        _to_date_multi(F.col("incident_date")).alias("incident_date"),
        F.lit(False).alias("incident_date_is_synthetic"),
        F.col("incident_type").alias("claim_type"),
        F.col("incident_severity").alias("severity"),
        F.col("total_claim_amount").cast(AMT).alias("total_claim_amount"),
        F.col("injury_claim").cast(AMT).alias("injury_claim"),
        F.col("property_claim").cast(AMT).alias("property_claim"),
        F.col("vehicle_claim").cast(AMT).alias("vehicle_claim"),
        F.col("auto_make").alias("auto_make"),
        F.col("auto_model").alias("auto_model"),
        F.col("auto_year").cast("int").alias("auto_year"),
        (F.upper(F.col("fraud_reported")) == "Y").alias("fraud"),
        F.col("insured_zip").alias("insured_zip"),
        F.col("incident_location").alias("incident_location"),
        F.col("age").cast("int").alias("policyholder_age"),
        F.col("insured_sex").alias("policyholder_sex"),
        F.lit(None).cast("string").alias("fault"),
        F.lit(None).cast("string").alias("vehicle_category"),
        F.col("_source_file"), F.col("_ingest_ts"),
    )

def _carclaims():
    df = spark.read.table(f"{BRONZE}.raw_carclaims")
    inc = F.make_date(F.col("Year").cast("int"), _month_num(F.col("Month")), F.lit(15))
    fraud = F.lower(F.trim(F.col("FraudFound"))).isin("1", "yes", "y", "true")
    return df.select(
        F.lit("carclaims").alias("source_system"),
        F.col("PolicyNumber").cast("string").alias("policy_number"),
        inc.alias("incident_date"),
        F.lit(True).alias("incident_date_is_synthetic"),
        F.lit(None).cast("string").alias("claim_type"),
        F.lit(None).cast("string").alias("severity"),
        F.lit(None).cast(AMT).alias("total_claim_amount"),
        F.lit(None).cast(AMT).alias("injury_claim"),
        F.lit(None).cast(AMT).alias("property_claim"),
        F.lit(None).cast(AMT).alias("vehicle_claim"),
        F.col("Make").alias("auto_make"),
        F.lit(None).cast("string").alias("auto_model"),
        F.lit(None).cast("int").alias("auto_year"),
        fraud.alias("fraud"),
        F.lit(None).cast("string").alias("insured_zip"),
        F.col("AccidentArea").alias("incident_location"),
        F.col("Age").cast("int").alias("policyholder_age"),
        F.col("Sex").alias("policyholder_sex"),
        F.col("Fault").alias("fault"),
        F.col("VehicleCategory").alias("vehicle_category"),
        F.col("_source_file"), F.col("_ingest_ts"),
    )

@dlt.view
def claim_enriched():
    base = _insurance().unionByName(_carclaims())
    cid = F.sha2(F.concat_ws("|",
        F.col("source_system"), F.coalesce(F.col("policy_number"), F.lit("")),
        F.coalesce(F.col("incident_date").cast("string"), F.lit("")),
        F.coalesce(F.col("total_claim_amount").cast("string"), F.lit("")),
        F.coalesce(F.col("auto_make"), F.lit("")),
        F.coalesce(F.col("incident_location"), F.lit("")),
        F.coalesce(F.col("policyholder_age").cast("string"), F.lit("")),
        F.coalesce(F.col("fault"), F.lit("")),
        F.coalesce(F.col("severity"), F.lit("")),
    ), 256)
    df = base.withColumn("claim_id", cid).dropDuplicates(["claim_id"])

    # seeded, deterministic synthetic lifecycle
    h = F.abs(F.hash(F.col("claim_id")))
    df = df.withColumn("fnol_date", F.date_add(F.col("incident_date"), (h % F.lit(4)) + F.lit(1)))
    roll = h % F.lit(100)
    status = (F.when(F.col("fraud"),
                     F.when(roll < 55, F.lit("denied")).otherwise(F.lit("under_review")))
                .otherwise(F.when(roll < 70, F.lit("closed"))
                            .when(roll < 90, F.lit("settled"))
                            .otherwise(F.lit("under_review"))))
    df = df.withColumn("claim_status", status)
    terminal = F.col("claim_status").isin("denied", "closed", "settled")
    df = df.withColumn("settlement_date",
                       F.when(terminal, F.date_add(F.col("fnol_date"), (h % F.lit(60)) + F.lit(5))))
    df = df.withColumn("cycle_time_days",
                       F.when(terminal, F.datediff(F.col("settlement_date"), F.col("fnol_date"))))

    # expectations -> quarantine reason (nothing dropped)
    reason = F.concat_ws("; ",
        F.when(F.col("total_claim_amount") < 0, F.lit("amount_negative")),
        F.when((F.col("source_system") == "insurance_claims") & F.col("claim_type").isNull(), F.lit("missing_claim_type")),
        F.when(F.col("policyholder_age").isNotNull() & (F.col("policyholder_age") < 16), F.lit("age_lt_16")),
        F.when(F.col("incident_date").isNotNull() & F.col("fnol_date").isNotNull() & (F.col("fnol_date") < F.col("incident_date")), F.lit("dates_unordered")),
        F.when(F.col("settlement_date").isNotNull() & (F.col("settlement_date") < F.col("fnol_date")), F.lit("settlement_before_fnol")),
    )
    df = df.withColumn("quarantine_reason", F.when(F.length(reason) > 0, reason))
    df = df.withColumn("is_valid", F.col("quarantine_reason").isNull())
    return df

_CLAIM_COLS = ["claim_id", "source_system", "policy_number", "incident_date",
    "incident_date_is_synthetic", "claim_type", "severity", "total_claim_amount",
    "injury_claim", "property_claim", "vehicle_claim", "auto_make", "auto_model",
    "auto_year", "fraud", "insured_zip", "incident_location", "policyholder_age",
    "policyholder_sex", "fault", "vehicle_category", "fnol_date", "claim_status",
    "settlement_date", "cycle_time_days", "_source_file", "_ingest_ts"]

@dlt.table(name="claim", comment="Conformed claims (insurance_claims + carclaims): typed, deduped, seeded synthetic lifecycle.")
@dlt.expect_all({"amount_non_negative": "total_claim_amount IS NULL OR total_claim_amount >= 0",
                 "age_valid": "policyholder_age IS NULL OR policyholder_age >= 16"})
def claim():
    return dlt.read("claim_enriched").filter("is_valid").select(*_CLAIM_COLS)

# ---------------------------------------------------------------- S3: quarantine
@dlt.table(name="claim_quarantine", comment="Claims failing Silver expectations, with reason. Nothing dropped.")
def claim_quarantine():
    return (dlt.read("claim_enriched").filter("NOT is_valid")
            .select("claim_id", "source_system", "policy_number", "incident_date",
                    "claim_type", "total_claim_amount", "policyholder_age",
                    "fnol_date", "settlement_date", "quarantine_reason"))

# ---------------------------------------------------------------- S2: status history (CDC)
@dlt.table(name="claim_status_history", comment="One row per status transition (derived synthetic lifecycle / CDC).")
def claim_status_history():
    c = dlt.read("claim")
    h = F.abs(F.hash(F.col("claim_id")))
    transitions = F.array(
        F.struct(F.lit("FNOL").alias("status"), F.col("fnol_date").alias("status_date"), F.lit(1).alias("seq")),
        F.struct(F.lit("under_review").alias("status"), F.date_add(F.col("fnol_date"), (h % F.lit(3)) + F.lit(1)).alias("status_date"), F.lit(2).alias("seq")),
        F.when(F.col("settlement_date").isNotNull(),
               F.struct(F.col("claim_status").alias("status"), F.col("settlement_date").alias("status_date"), F.lit(3).alias("seq"))),
    )
    ex = c.select("claim_id", "source_system", F.explode(transitions).alias("t")).filter("t IS NOT NULL")
    return ex.select("claim_id", "source_system",
                     F.col("t.status").alias("status"),
                     F.col("t.status_date").alias("status_date"),
                     F.col("t.seq").alias("seq"))

# ---------------------------------------------------------------- claim_severity
@dlt.table(name="claim_severity", comment="Conformed claim amounts: freMTPL2sev + Spanish by-type.")
def claim_severity():
    sev = spark.read.table(f"{BRONZE}.raw_claim_severity").select(
        F.lit("freMTPL2sev").alias("source_system"),
        F.col("IDpol").cast("string").alias("policy_id"),
        F.col("ClaimAmount").cast(AMT).alias("claim_amount"),
        F.lit(None).cast("string").alias("claim_type"),
        F.lit(None).cast(AMT).alias("year_total_cost"),
    )
    byt = spark.read.table(f"{BRONZE}.raw_claims_by_type").select(
        F.lit("spanish_by_type").alias("source_system"),
        F.col("ID").cast("string").alias("policy_id"),
        F.col("Cost_claims_by_type").cast(AMT).alias("claim_amount"),
        F.col("Claims_type").alias("claim_type"),
        F.col("Cost_claims_year").cast(AMT).alias("year_total_cost"),
    )
    return sev.unionByName(byt)

# ---------------------------------------------------------------- S4: SCD2 dims (APPLY CHANGES)
@dlt.view
def policyholder_src():
    ins = spark.readStream.table(f"{BRONZE}.raw_insurance_claims").select(
        F.col("policy_number").cast("string").alias("policy_number"),
        F.lit("insurance_claims").alias("source_system"),
        F.col("age").cast("int").alias("age"),
        F.col("insured_sex").alias("sex"),
        F.col("insured_zip").alias("zip"),
        F.col("policy_state").alias("state"),
        F.col("insured_education_level").alias("education"),
        F.col("insured_occupation").alias("occupation"),
        F.col("_ingest_ts").alias("seq_ts"))
    car = spark.readStream.table(f"{BRONZE}.raw_carclaims").select(
        F.col("PolicyNumber").cast("string").alias("policy_number"),
        F.lit("carclaims").alias("source_system"),
        F.col("Age").cast("int").alias("age"),
        F.col("Sex").alias("sex"),
        F.lit(None).cast("string").alias("zip"),
        F.lit(None).cast("string").alias("state"),
        F.lit(None).cast("string").alias("education"),
        F.lit(None).cast("string").alias("occupation"),
        F.col("_ingest_ts").alias("seq_ts"))
    return ins.unionByName(car).dropDuplicates(["policy_number", "source_system"])

dlt.create_streaming_table("dim_policyholder", comment="SCD2 policyholder dimension (APPLY CHANGES INTO).")
dlt.apply_changes(
    target="dim_policyholder", source="policyholder_src",
    keys=["policy_number", "source_system"], sequence_by=F.col("seq_ts"),
    stored_as_scd_type=2,
)

@dlt.view
def vehicle_src():
    ins = spark.readStream.table(f"{BRONZE}.raw_insurance_claims").select(
        F.col("auto_make").alias("make"), F.col("auto_model").alias("model"),
        F.col("auto_year").cast("int").alias("model_year"),
        F.lit(None).cast("string").alias("category"),
        F.col("_ingest_ts").alias("seq_ts"))
    car = spark.readStream.table(f"{BRONZE}.raw_carclaims").select(
        F.col("Make").alias("make"), F.lit(None).cast("string").alias("model"),
        F.lit(None).cast("int").alias("model_year"),
        F.col("VehicleCategory").alias("category"),
        F.col("_ingest_ts").alias("seq_ts"))
    u = ins.unionByName(car)
    vk = F.sha2(F.concat_ws("|",
        F.coalesce(F.col("make"), F.lit("")), F.coalesce(F.col("model"), F.lit("")),
        F.coalesce(F.col("model_year").cast("string"), F.lit("")),
        F.coalesce(F.col("category"), F.lit(""))), 256)
    return u.withColumn("vehicle_key", vk).dropDuplicates(["vehicle_key"])

dlt.create_streaming_table("dim_vehicle", comment="SCD2 vehicle dimension (APPLY CHANGES INTO).")
dlt.apply_changes(
    target="dim_vehicle", source="vehicle_src",
    keys=["vehicle_key"], sequence_by=F.col("seq_ts"),
    stored_as_scd_type=2,
)
