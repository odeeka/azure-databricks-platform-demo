# Databricks notebook source
# =============================================================================
# 01_bronze_ingestion
# =============================================================================
# Purpose: Ingest raw JSON sensor data from ADLS Gen2 into a Bronze Delta table.
#
# Pattern: Raw JSON files → Bronze Delta table (append-only)
#
# The Bronze layer preserves the raw data as-is, adding only:
#   - _source_file: which file the record came from
#   - _ingested_at: when the record was ingested
#
# This notebook uses Auto Loader (cloudFiles) for efficient incremental
# ingestion. Auto Loader automatically picks up new files and tracks which
# files have already been processed via a checkpoint.
#
# With Unity Catalog:
#   Input:  abfss://raw@<storage>/sensors/**/*.json  (NDJSON files)
#   Output: {catalog}.bronze.sensor_readings          (managed Delta table)
#
# Without Unity Catalog (legacy):
#   Input:  abfss://raw@<storage>/sensors/**/*.json
#   Output: abfss://bronze@<storage>/sensor_readings  (external Delta table)
# =============================================================================

# COMMAND ----------

# MAGIC %md
# MAGIC # Bronze Layer — Raw Data Ingestion
# MAGIC
# MAGIC Ingests raw JSON sensor data into a Bronze Delta table.
# MAGIC
# MAGIC **What this does:**
# MAGIC - Reads new JSON files from the `raw` container using Auto Loader
# MAGIC - Adds metadata columns (`_source_file`, `_ingested_at`)
# MAGIC - Writes to a managed Delta table (Unity Catalog) or external path
# MAGIC - Tracks progress via checkpoint (won't re-process old files)

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, TimestampType
)

# COMMAND ----------

# MAGIC %run ./_config

# COMMAND ----------

# ADLS paths — raw input is always from ADLS (external to UC)
RAW_PATH = f"abfss://raw@{STORAGE_ACCOUNT}.dfs.core.windows.net/sensors/"
CHECKPOINT_PATH = f"abfss://bronze@{STORAGE_ACCOUNT}.dfs.core.windows.net/_checkpoints/sensor_readings"

# Output target: UC managed table or external ADLS path
if USE_UC:
    BRONZE_TABLE = f"{CATALOG}.bronze.sensor_readings"
    print(f"Mode:          Unity Catalog")
    print(f"Bronze table:  {BRONZE_TABLE}")
else:
    BRONZE_PATH = f"abfss://bronze@{STORAGE_ACCOUNT}.dfs.core.windows.net/sensor_readings"
    print(f"Mode:          Legacy (abfss:// paths)")
    print(f"Bronze path:   {BRONZE_PATH}")

print(f"Raw input:     {RAW_PATH}")
print(f"Checkpoint:    {CHECKPOINT_PATH}")

# COMMAND ----------

# Define the expected schema for the raw JSON data
# Defining an explicit schema is a best practice — it:
#   1. Makes ingestion faster (no schema inference needed)
#   2. Prevents unexpected schema changes from breaking the pipeline
#   3. Documents the expected data format
raw_schema = StructType([
    StructField("event_id", StringType(), True),
    StructField("device_id", StringType(), True),
    StructField("timestamp", StringType(), True),  # Ingested as string, parsed in Silver
    StructField("temperature", DoubleType(), True),
    StructField("humidity", DoubleType(), True),
    StructField("pm25", DoubleType(), True),
    StructField("no2", DoubleType(), True),
    StructField("co", DoubleType(), True),
    StructField("latitude", DoubleType(), True),
    StructField("longitude", DoubleType(), True),
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Batch Ingestion (Auto Loader)

# COMMAND ----------

# Read raw JSON files using Auto Loader
df_raw = (
    spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.schemaLocation", CHECKPOINT_PATH + "/_schema")
    .schema(raw_schema)
    .load(RAW_PATH)
)

# Add metadata columns — these help with debugging and data lineage
# Note: input_file_name() is not supported in Unity Catalog mode.
# Use _metadata.file_path instead (available with Auto Loader / cloudFiles).
df_bronze = (
    df_raw
    .withColumn("_source_file", F.col("_metadata.file_path"))
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_ingestion_date", F.current_date())
)

# Write to Bronze Delta table
if USE_UC:
    # Unity Catalog: write to a managed table (UC handles storage location)
    bronze_write = (
        df_bronze.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", CHECKPOINT_PATH)
        .option("mergeSchema", "true")
        .trigger(availableNow=True)
        .toTable(BRONZE_TABLE)
    )
else:
    # Legacy: write to explicit ADLS path
    bronze_write = (
        df_bronze.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", CHECKPOINT_PATH)
        .option("mergeSchema", "true")
        .partitionBy("_ingestion_date")
        .trigger(availableNow=True)
        .start(BRONZE_PATH)
    )

bronze_write.awaitTermination()
print("✓ Bronze ingestion complete!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Bronze Table

# COMMAND ----------

# Read back the Bronze table and show stats
if USE_UC:
    df_bronze_check = spark.table(BRONZE_TABLE)
    table_ref = BRONZE_TABLE
else:
    df_bronze_check = spark.read.format("delta").load(BRONZE_PATH)
    table_ref = BRONZE_PATH

record_count = df_bronze_check.count()
device_count = df_bronze_check.select("device_id").distinct().count()

print(f"✓ Bronze table: {table_ref}")
print(f"  Total records: {record_count}")
print(f"  Unique devices: {device_count}")
print(f"  Columns: {df_bronze_check.columns}")

df_bronze_check.show(5, truncate=False)

# COMMAND ----------

df_bronze_check.describe("temperature", "humidity", "pm25", "no2", "co").show()
