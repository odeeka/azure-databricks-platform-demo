# Databricks notebook source
# =============================================================================
# 02_silver_transformation
# =============================================================================
# Purpose: Clean, validate, and normalize Bronze data into the Silver layer.
#
# Transformations applied:
#   1. Parse timestamp string → proper TimestampType
#   2. Remove duplicate event_ids (deduplication)
#   3. Filter out records with null required fields
#   4. Validate ranges (e.g., humidity 0-100, temperature -50 to 60)
#   5. Flag anomalies but keep them in a separate quarantine table
#   6. Standardize column names and types
#
# With Unity Catalog:
#   Input:  {catalog}.bronze.sensor_readings
#   Output: {catalog}.silver.sensor_readings_clean
#           {catalog}.silver.sensor_readings_quarantine
#
# Without Unity Catalog (legacy):
#   Input:  abfss://bronze@<storage>/sensor_readings
#   Output: abfss://silver@<storage>/sensor_readings_clean
#           abfss://silver@<storage>/sensor_readings_quarantine
# =============================================================================

# COMMAND ----------

# MAGIC %md
# MAGIC # Silver Layer — Data Cleaning & Validation
# MAGIC
# MAGIC Transforms raw Bronze data into clean, validated Silver tables.
# MAGIC
# MAGIC **Rules:**
# MAGIC - Deduplicate by `event_id`
# MAGIC - Parse timestamps
# MAGIC - Validate value ranges
# MAGIC - Quarantine bad records (instead of silently dropping them)

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import TimestampType
from delta.tables import DeltaTable

# COMMAND ----------

# MAGIC %run ./_config

# COMMAND ----------

if USE_UC:
    BRONZE_TABLE = f"{CATALOG}.bronze.sensor_readings"
    SILVER_CLEAN_TABLE = f"{CATALOG}.silver.sensor_readings_clean"
    SILVER_QUARANTINE_TABLE = f"{CATALOG}.silver.sensor_readings_quarantine"
    print(f"Mode:              Unity Catalog")
    print(f"Bronze input:      {BRONZE_TABLE}")
    print(f"Silver clean:      {SILVER_CLEAN_TABLE}")
    print(f"Silver quarantine: {SILVER_QUARANTINE_TABLE}")
else:
    BRONZE_PATH = f"abfss://bronze@{STORAGE_ACCOUNT}.dfs.core.windows.net/sensor_readings"
    SILVER_CLEAN_PATH = f"abfss://silver@{STORAGE_ACCOUNT}.dfs.core.windows.net/sensor_readings_clean"
    SILVER_QUARANTINE_PATH = f"abfss://silver@{STORAGE_ACCOUNT}.dfs.core.windows.net/sensor_readings_quarantine"
    print(f"Mode:              Legacy (abfss://)")
    print(f"Bronze input:      {BRONZE_PATH}")
    print(f"Silver clean:      {SILVER_CLEAN_PATH}")
    print(f"Silver quarantine: {SILVER_QUARANTINE_PATH}")

# COMMAND ----------

# Read the Bronze table
if USE_UC:
    df_bronze = spark.table(BRONZE_TABLE)
else:
    df_bronze = spark.read.format("delta").load(BRONZE_PATH)
print(f"Bronze records: {df_bronze.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Parse Timestamps & Deduplicate

# COMMAND ----------

# Parse the ISO timestamp string into a proper Spark TimestampType
# Drop duplicates based on event_id (the data generator creates unique UUIDs,
# but in real systems, retries can cause duplicates)
df_parsed = (
    df_bronze
    .withColumn("event_timestamp", F.to_timestamp("timestamp"))
    .withColumn("event_hour", F.date_trunc("hour", "event_timestamp"))
    .dropDuplicates(["event_id"])
)

print(f"After dedup: {df_parsed.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Data Quality Validation
# MAGIC
# MAGIC Define what "valid" means for each field. Records failing these checks
# MAGIC go to quarantine; passing records go to the clean Silver table.

# COMMAND ----------

# Define validation rules as boolean columns
# Each rule produces True (valid) or False (invalid)
df_validated = (
    df_parsed
    .withColumn("_valid_timestamp", F.col("event_timestamp").isNotNull())
    .withColumn("_valid_device_id", F.col("device_id").isNotNull() & (F.length("device_id") > 0))
    .withColumn("_valid_temperature",
        F.col("temperature").isNotNull() &
        (F.col("temperature") >= -50) &
        (F.col("temperature") <= 60)
    )
    .withColumn("_valid_humidity",
        F.col("humidity").isNotNull() &
        (F.col("humidity") >= 0) &
        (F.col("humidity") <= 100)
    )
    .withColumn("_valid_pm25",
        F.col("pm25").isNotNull() &
        (F.col("pm25") >= 0) &
        (F.col("pm25") <= 500)  # WHO AQI scale goes up to ~500
    )
    .withColumn("_valid_no2",
        F.col("no2").isNotNull() &
        (F.col("no2") >= 0) &
        (F.col("no2") <= 400)
    )
    .withColumn("_valid_co",
        F.col("co").isNotNull() &
        (F.col("co") >= 0) &
        (F.col("co") <= 50)
    )
    # A record is valid only if ALL checks pass
    .withColumn("_is_valid",
        F.col("_valid_timestamp") &
        F.col("_valid_device_id") &
        F.col("_valid_temperature") &
        F.col("_valid_humidity") &
        F.col("_valid_pm25") &
        F.col("_valid_no2") &
        F.col("_valid_co")
    )
)

# Count valid vs invalid
valid_count = df_validated.filter(F.col("_is_valid")).count()
invalid_count = df_validated.filter(~F.col("_is_valid")).count()
print(f"Valid records:   {valid_count}")
print(f"Invalid records: {invalid_count}")
print(f"Quality score:   {valid_count / (valid_count + invalid_count) * 100:.1f}%")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Split Clean vs. Quarantined Records

# COMMAND ----------

# Clean records — ready for analytics
# Select only the business columns (drop internal validation flags)
df_clean = (
    df_validated
    .filter(F.col("_is_valid"))
    .select(
        "event_id",
        "device_id",
        "event_timestamp",
        "event_hour",
        "temperature",
        "humidity",
        "pm25",
        "no2",
        "co",
        "latitude",
        "longitude",
        "_source_file",
        "_ingested_at",
    )
    .withColumn("_cleaned_at", F.current_timestamp())
)

# Quarantined records — kept for investigation
# Include the validation flags so you can see WHY each record was quarantined
df_quarantine = (
    df_validated
    .filter(~F.col("_is_valid"))
    .withColumn("_quarantined_at", F.current_timestamp())
    .withColumn("_quarantine_reason",
        F.concat_ws(", ",
            F.when(~F.col("_valid_timestamp"), F.lit("invalid_timestamp")),
            F.when(~F.col("_valid_device_id"), F.lit("invalid_device_id")),
            F.when(~F.col("_valid_temperature"), F.lit("invalid_temperature")),
            F.when(~F.col("_valid_humidity"), F.lit("invalid_humidity")),
            F.when(~F.col("_valid_pm25"), F.lit("invalid_pm25")),
            F.when(~F.col("_valid_no2"), F.lit("invalid_no2")),
            F.when(~F.col("_valid_co"), F.lit("invalid_co")),
        )
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Write Silver Tables

# COMMAND ----------

# Write clean Silver table — use MERGE to preserve historical data
if USE_UC:
    if table_exists(SILVER_CLEAN_TABLE):
        delta_table = DeltaTable.forName(spark, SILVER_CLEAN_TABLE)
        (
            delta_table.alias("target")
            .merge(df_clean.alias("source"), "target.event_id = source.event_id")
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute()
        )
    else:
        df_clean.write.format("delta").saveAsTable(SILVER_CLEAN_TABLE)
else:
    if path_exists(SILVER_CLEAN_PATH):
        delta_table = DeltaTable.forPath(spark, SILVER_CLEAN_PATH)
        (
            delta_table.alias("target")
            .merge(df_clean.alias("source"), "target.event_id = source.event_id")
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute()
        )
    else:
        (
            df_clean.write
            .format("delta")
            .partitionBy("event_hour")
            .save(SILVER_CLEAN_PATH)
        )
print(f"✓ Silver clean table written: {df_clean.count()} records")

# Write quarantine table — APPEND to preserve history of bad records
if df_quarantine.count() > 0:
    if USE_UC:
        (
            df_quarantine.write
            .format("delta")
            .mode("append")
            .saveAsTable(SILVER_QUARANTINE_TABLE)
        )
    else:
        (
            df_quarantine.write
            .format("delta")
            .mode("append")
            .save(SILVER_QUARANTINE_PATH)
        )
    print(f"✓ Silver quarantine table written: {df_quarantine.count()} records")
else:
    print("✓ No quarantined records (all data was clean)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Silver Tables

# COMMAND ----------

# Show clean data sample
print("=== Silver Clean Table ===")
if USE_UC:
    df_silver = spark.table(SILVER_CLEAN_TABLE)
else:
    df_silver = spark.read.format("delta").load(SILVER_CLEAN_PATH)
print(f"Records: {df_silver.count()}")
df_silver.show(5, truncate=False)

# Show quarantine data if any
try:
    print("\n=== Silver Quarantine Table ===")
    if USE_UC:
        df_quarantine_check = spark.table(SILVER_QUARANTINE_TABLE)
    else:
        df_quarantine_check = spark.read.format("delta").load(SILVER_QUARANTINE_PATH)
    print(f"Records: {df_quarantine_check.count()}")
    df_quarantine_check.select("event_id", "device_id", "temperature", "humidity", "pm25", "_quarantine_reason").show(10, truncate=False)
except Exception:
    print("No quarantine table (all records passed validation)")

# COMMAND ----------

# Data quality summary
print("=== Data Quality Summary ===")
df_silver.describe("temperature", "humidity", "pm25", "no2", "co").show()
