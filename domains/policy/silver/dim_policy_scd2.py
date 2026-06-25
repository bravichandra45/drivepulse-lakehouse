# Databricks notebook source
# COMMAND ----------
# MAGIC %md
# MAGIC # dim_policy_scd2 — SCD2 policy dimension (renewals change attributes over time)
# COMMAND ----------
import dlt
# TODO(claude-code): apply_changes SCD2 on policy_id, sequence_by endorsement_ts.
