# Databricks notebook source
# =============================================================================
# 00_setup_storage_access
# =============================================================================
# Purpose: Configures Databricks to access the ADLS Gen2 storage account
#          and sets up Unity Catalog context.
#
# With Unity Catalog enabled:
#   - Storage access is handled by the Access Connector (managed identity)
#   - No storage keys needed for Delta tables in the catalog!
#   - Storage keys are only needed for reading RAW JSON (external location)
#
# Without Unity Catalog (fallback):
#   - Uses storage account key for all ADLS access via Spark config
#
# Run this notebook ONCE before running the pipeline notebooks.
# =============================================================================

# COMMAND ----------

# MAGIC %md
# MAGIC # Storage Access & Catalog Configuration
# MAGIC
# MAGIC This notebook sets up:
# MAGIC 1. The Unity Catalog catalog and default schema
# MAGIC 2. Storage access for reading raw data (external location or key-based)
# MAGIC
# MAGIC **Get values from Terraform:**
# MAGIC ```bash
# MAGIC cd terraform/environments/dev
# MAGIC terraform output storage_account_name
# MAGIC terraform output catalog_name
# MAGIC terraform output -raw storage_account_key   # Only needed if UC external location isn't configured
# MAGIC ```

# COMMAND ----------

# Configuration — update these from your Terraform output
STORAGE_ACCOUNT_NAME = "stdbdemodevweu"   # From: terraform output storage_account_name
CATALOG_NAME = "dev"                       # From: terraform output catalog_name
USE_UNITY_CATALOG = True                   # Set to False to use legacy abfss:// paths

# COMMAND ----------

# With Unity Catalog + External Location, the Access Connector's managed identity
# handles storage auth automatically — no keys needed!
#
# Only set a storage key if UC external location is NOT configured (legacy mode).
if not USE_UNITY_CATALOG:
    STORAGE_ACCOUNT_KEY = "YOUR_KEY_HERE"  # From: terraform output -raw storage_account_key
    spark.conf.set(
        f"fs.azure.account.key.{STORAGE_ACCOUNT_NAME}.dfs.core.windows.net",
        STORAGE_ACCOUNT_KEY
    )
    print(f"✓ Configured storage access with account key: {STORAGE_ACCOUNT_NAME}")
else:
    print(f"✓ Unity Catalog mode — storage access via managed identity (no key needed)")

# COMMAND ----------

# Set Unity Catalog context
if USE_UNITY_CATALOG:
    spark.sql(f"USE CATALOG {CATALOG_NAME}")
    print(f"✓ Using Unity Catalog: {CATALOG_NAME}")
    print(f"  Available schemas: bronze, silver, gold")
    print(f"  Table references: {CATALOG_NAME}.bronze.sensor_readings")
    print(f"                    {CATALOG_NAME}.silver.sensor_readings_clean")
    print(f"                    {CATALOG_NAME}.gold.hourly_metrics")
else:
    print("ℹ Unity Catalog disabled — using direct abfss:// paths")

# COMMAND ----------

# Quick test — list files in the raw container
try:
    files = dbutils.fs.ls(f"abfss://raw@{STORAGE_ACCOUNT_NAME}.dfs.core.windows.net/")
    print(f"✓ Successfully connected! Found {len(files)} items in raw container.")
    for f in files[:10]:
        print(f"  {f.name}")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    print("  Make sure:")
    print("  1. The storage account name is correct")
    print("  2. Unity Catalog external location is configured (or storage key is set)")
    print("  3. The data generator has been run at least once")

# COMMAND ----------

# Store config as widgets for other notebooks
dbutils.widgets.text("storage_account_name", STORAGE_ACCOUNT_NAME, "Storage Account Name")
dbutils.widgets.text("catalog_name", CATALOG_NAME, "Catalog Name")
dbutils.widgets.dropdown("use_unity_catalog", str(USE_UNITY_CATALOG), ["True", "False"], "Use Unity Catalog")
print(f"✓ Widgets set: storage={STORAGE_ACCOUNT_NAME}, catalog={CATALOG_NAME}, uc={USE_UNITY_CATALOG}")
