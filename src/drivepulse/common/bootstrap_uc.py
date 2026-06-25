# Databricks notebook source
# COMMAND ----------
# MAGIC %md
# MAGIC # bootstrap_uc — create catalogs + medallion schemas, set grants
# MAGIC Run once per target. Idempotent: uses CREATE ... IF NOT EXISTS.
# COMMAND ----------
dbutils.widgets.text("catalog_telematics", "dev_telematics")
dbutils.widgets.text("catalog_policy", "dev_policy")
dbutils.widgets.text("catalog_claims", "dev_claims")

catalogs = [
    dbutils.widgets.get("catalog_telematics"),
    dbutils.widgets.get("catalog_policy"),
    dbutils.widgets.get("catalog_claims"),
]
schemas = ["bronze", "silver", "gold", "docs"]

# TODO(claude-code): add COMMENT, OWNER, and grants per owning team.
for cat in catalogs:
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {cat}")
    for sch in schemas:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {cat}.{sch}")
        print(f"ensured {cat}.{sch}")
