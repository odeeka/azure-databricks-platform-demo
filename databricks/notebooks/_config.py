# Databricks notebook source
# =============================================================================
# _config — Shared configuration for all pipeline notebooks
# =============================================================================
# This notebook is called via %run from all pipeline notebooks.
# It defines:
#   - Databricks widgets (user-editable parameters)
#   - Common configuration variables (STORAGE_ACCOUNT, CATALOG, USE_UC)
#   - Utility functions used across multiple notebooks
#
# Usage (from any notebook):
#   %run ./_config
#
# When called from 04_run_full_pipeline via dbutils.notebook.run(),
# the widget values are overridden by the passed arguments.
# =============================================================================

# COMMAND ----------

# Widget definitions — editable defaults for standalone execution.
# Overridden when called from the pipeline orchestrator (04_run_full_pipeline).
dbutils.widgets.text("storage_account_name", "stdbdemodevweu", "Storage Account")
dbutils.widgets.text("catalog_name", "dev", "Catalog Name")
dbutils.widgets.dropdown("use_unity_catalog", "True", ["True", "False"], "Use Unity Catalog")

# COMMAND ----------

# Core configuration — derived from widgets
STORAGE_ACCOUNT = dbutils.widgets.get("storage_account_name")
CATALOG = dbutils.widgets.get("catalog_name")
USE_UC = dbutils.widgets.get("use_unity_catalog") == "True"

print(f"Pipeline Configuration:")
print(f"  Storage Account: {STORAGE_ACCOUNT}")
print(f"  Catalog:         {CATALOG}")
print(f"  Unity Catalog:   {USE_UC}")

# COMMAND ----------

def table_exists(table_name):
    """Check if a Unity Catalog table exists."""
    try:
        spark.table(table_name)
        return True
    except Exception:
        return False

def path_exists(path):
    """Check if a Delta table exists at an ADLS path."""
    try:
        dbutils.fs.ls(path)
        return True
    except Exception:
        return False
