# Databricks notebook source
# COMMAND ----------
# MAGIC %md
# MAGIC # build_mart_claim_360 — CROSS-DOMAIN mart (lives in prod_claims.gold)
# MAGIC Joins claim + policy (prod_policy) + trip telemetry at time-of-loss
# MAGIC (prod_telematics) + federated weather. The fraud-detection / fast-settle payoff.
# MAGIC Read other domains by three-part name ONLY (no copying).
# COMMAND ----------
# TODO(claude-code): build mart_claim_360 reading prod_telematics.gold.fact_trip
# and prod_policy.gold.dim_policy via three-part names.
