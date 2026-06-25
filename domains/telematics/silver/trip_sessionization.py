# Databricks notebook source
# COMMAND ----------
# MAGIC %md
# MAGIC # trip_sessionization — Lakeflow: assemble trips from raw telemetry
# MAGIC Stateful sessionization on ignition on/off (or time-gap). Expectations:
# MAGIC GPS sanity, speed/accel bounds, monotonic timestamps. Failed rows -> quarantine.
# COMMAND ----------
import dlt  # Lakeflow Declarative Pipelines decorators
# TODO(claude-code): @dlt.table for silver.trip + @dlt.expect_or_drop rules;
# route failures to silver.trip_quarantine.
