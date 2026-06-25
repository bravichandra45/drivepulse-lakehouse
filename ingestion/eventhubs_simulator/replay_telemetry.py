# Databricks notebook source
# COMMAND ----------
# MAGIC %md
# MAGIC # replay_telemetry — replay VED chronologically into Azure Event Hubs at Nx speed
# MAGIC Simulates a live connected-vehicle fleet. Read EH connection string from a
# MAGIC secret scope, never inline.
# COMMAND ----------
dbutils.widgets.text("speedup", "50")
# TODO(claude-code): read VED from bronze landing or data/, sort by timestamp,
# emit to Event Hubs (Kafka endpoint) at speedup x wall-clock. Idempotent + resumable.
