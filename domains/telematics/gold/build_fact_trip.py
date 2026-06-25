# Databricks notebook source
# COMMAND ----------
# MAGIC %md
# MAGIC # build_fact_trip — gold star: fact_trip (one row per trip) + enrichment
# MAGIC Joins silver trip to conformed dims + federated weather at trip time.
# COMMAND ----------
# TODO(claude-code): MERGE into {catalog_telematics}.gold.fact_trip.
