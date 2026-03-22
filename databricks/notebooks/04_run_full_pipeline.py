# Databricks notebook source
# =============================================================================
# 04_run_full_pipeline
# =============================================================================
# Purpose: Orchestrator notebook that runs the complete medallion pipeline
#          end-to-end: Bronze → Silver → Gold
#
# This is a convenience notebook for demos — it calls each layer's notebook
# in sequence using dbutils.notebook.run().
#
# Usage: Just run this notebook with the storage_account_name widget set.
#        For Unity Catalog mode, also set catalog_name and use_unity_catalog.
# =============================================================================

# COMMAND ----------

# MAGIC %md
# MAGIC # Full Pipeline Orchestrator
# MAGIC
# MAGIC Runs the complete Bronze → Silver → Gold pipeline in sequence.
# MAGIC
# MAGIC **Prerequisites:**
# MAGIC 1. Run `00_setup_storage_access` first to configure credentials
# MAGIC 2. Run the Python data generator to create raw data
# MAGIC
# MAGIC **What happens:**
# MAGIC 1. Bronze: Ingest raw JSON → Delta table
# MAGIC 2. Silver: Clean, validate, deduplicate
# MAGIC 3. Gold: Aggregate into analytics tables

# COMMAND ----------

import time

# COMMAND ----------

# Widget definitions — editable at the top of the notebook
dbutils.widgets.text("storage_account_name", "stdbdemodevweu", "Storage Account")
dbutils.widgets.text("catalog_name", "dev", "Catalog Name")
dbutils.widgets.dropdown("use_unity_catalog", "True", ["True", "False"], "Use Unity Catalog")

# COMMAND ----------

STORAGE_ACCOUNT = dbutils.widgets.get("storage_account_name")
CATALOG = dbutils.widgets.get("catalog_name")
USE_UC = dbutils.widgets.get("use_unity_catalog")
USE_UC_BOOL = USE_UC == "True"

print(f"Storage account: {STORAGE_ACCOUNT}")
if USE_UC_BOOL:
    print(f"Unity Catalog:   {CATALOG}")
print(f"Starting full pipeline run...")
print("=" * 60)

# Common arguments passed to every child notebook
NOTEBOOK_ARGS = {
    "storage_account_name": STORAGE_ACCOUNT,
    "catalog_name": CATALOG,
    "use_unity_catalog": USE_UC,
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Bronze Ingestion

# COMMAND ----------

print("▶ Running Bronze ingestion...")
start = time.time()
dbutils.notebook.run(
    "./01_bronze_ingestion",
    timeout_seconds=600,
    arguments=NOTEBOOK_ARGS
)
elapsed = time.time() - start
print(f"✓ Bronze complete ({elapsed:.1f}s)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Silver Transformation

# COMMAND ----------

print("▶ Running Silver transformation...")
start = time.time()
dbutils.notebook.run(
    "./02_silver_transformation",
    timeout_seconds=600,
    arguments=NOTEBOOK_ARGS
)
elapsed = time.time() - start
print(f"✓ Silver complete ({elapsed:.1f}s)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Gold Aggregation

# COMMAND ----------

print("▶ Running Gold aggregation...")
start = time.time()
dbutils.notebook.run(
    "./03_gold_aggregation",
    timeout_seconds=600,
    arguments=NOTEBOOK_ARGS
)
elapsed = time.time() - start
print(f"✓ Gold complete ({elapsed:.1f}s)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pipeline Complete!

# COMMAND ----------

print("=" * 60)
print("✓ FULL PIPELINE COMPLETE")
print("=" * 60)
print()

if USE_UC_BOOL:
    print(f"Tables created (Unity Catalog — {CATALOG}):")
    print(f"  Bronze: {CATALOG}.bronze.sensor_readings")
    print(f"  Silver: {CATALOG}.silver.sensor_readings_clean")
    print(f"  Silver: {CATALOG}.silver.sensor_readings_quarantine")
    print(f"  Gold:   {CATALOG}.gold.hourly_metrics")
    print(f"  Gold:   {CATALOG}.gold.device_summary")
    print(f"  Gold:   {CATALOG}.gold.aqi_alerts")
else:
    print("Tables created (Legacy abfss):")
    print(f"  Bronze: abfss://bronze@{STORAGE_ACCOUNT}.dfs.core.windows.net/sensor_readings")
    print(f"  Silver: abfss://silver@{STORAGE_ACCOUNT}.dfs.core.windows.net/sensor_readings_clean")
    print(f"  Silver: abfss://silver@{STORAGE_ACCOUNT}.dfs.core.windows.net/sensor_readings_quarantine")
    print(f"  Gold:   abfss://gold@{STORAGE_ACCOUNT}.dfs.core.windows.net/hourly_metrics")
    print(f"  Gold:   abfss://gold@{STORAGE_ACCOUNT}.dfs.core.windows.net/device_summary")
    print(f"  Gold:   abfss://gold@{STORAGE_ACCOUNT}.dfs.core.windows.net/aqi_alerts")
