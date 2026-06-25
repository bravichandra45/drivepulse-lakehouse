# Databricks notebook source
# COMMAND ----------
# MAGIC %md
# MAGIC # dim_driver_scd2 — SCD2 conformed driver dimension via APPLY CHANGES INTO
# COMMAND ----------
import dlt
# TODO(claude-code): dlt.create_streaming_table("dim_driver");
# dlt.apply_changes(target="dim_driver", source=..., keys=["driver_id"],
#   sequence_by="effective_ts", stored_as_scd_type=2)
