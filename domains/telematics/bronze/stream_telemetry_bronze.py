# Databricks notebook source
# COMMAND ----------
# MAGIC %md
# MAGIC # stream_telemetry_bronze — Structured Streaming from Event Hubs -> bronze Delta
# MAGIC Append-only, checkpointed. Schema-on-read; keep raw payload + ingest metadata.
# COMMAND ----------
# TODO(claude-code): readStream from Event Hubs (kafka format), writeStream to
# {catalog_telematics}.bronze.raw_telemetry with checkpointLocation.
