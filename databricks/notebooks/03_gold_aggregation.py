# Databricks notebook source
# =============================================================================
# 03_gold_aggregation
# =============================================================================
# Purpose: Aggregate Silver data into Gold analytics-ready tables.
#
# Gold tables are optimized for specific analytical use cases:
#   1. Hourly pollution metrics per device
#   2. Device summary statistics
#   3. Air quality index (AQI) classifications
#
# These tables are what dashboards, reports, and data consumers query.
#
# Unity Catalog mode:
#   Input:  <catalog>.silver.sensor_readings_clean
#   Output: <catalog>.gold.hourly_metrics
#           <catalog>.gold.device_summary
#           <catalog>.gold.aqi_alerts
#
# Legacy (abfss) mode:
#   Input:  abfss://silver@<storage>/sensor_readings_clean (Delta)
#   Output: abfss://gold@<storage>/hourly_metrics (Delta)
#           abfss://gold@<storage>/device_summary (Delta)
#           abfss://gold@<storage>/aqi_alerts (Delta)
# =============================================================================

# COMMAND ----------

# MAGIC %md
# MAGIC # Gold Layer — Analytics Aggregation
# MAGIC
# MAGIC Creates analytics-ready tables from clean Silver data.
# MAGIC
# MAGIC **Tables produced:**
# MAGIC 1. `hourly_metrics` — Hourly average pollution metrics per device
# MAGIC 2. `device_summary` — Overall device health and statistics
# MAGIC 3. `aqi_alerts` — Hours where air quality exceeded WHO guidelines

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window
from delta.tables import DeltaTable

# COMMAND ----------

# MAGIC %run ./_config

# COMMAND ----------

# Unity Catalog managed table names
SILVER_TABLE      = f"{CATALOG}.silver.sensor_readings_clean"
GOLD_HOURLY_TABLE = f"{CATALOG}.gold.hourly_metrics"
GOLD_DEVICE_TABLE = f"{CATALOG}.gold.device_summary"
GOLD_AQI_TABLE    = f"{CATALOG}.gold.aqi_alerts"

# Legacy abfss paths
SILVER_PATH = f"abfss://silver@{STORAGE_ACCOUNT}.dfs.core.windows.net/sensor_readings_clean"
GOLD_HOURLY_PATH = f"abfss://gold@{STORAGE_ACCOUNT}.dfs.core.windows.net/hourly_metrics"
GOLD_DEVICE_PATH = f"abfss://gold@{STORAGE_ACCOUNT}.dfs.core.windows.net/device_summary"
GOLD_AQI_PATH = f"abfss://gold@{STORAGE_ACCOUNT}.dfs.core.windows.net/aqi_alerts"

if USE_UC:
    print(f"Mode: Unity Catalog")
    print(f"Silver input:   {SILVER_TABLE}")
    print(f"Gold outputs:")
    print(f"  hourly_metrics:  {GOLD_HOURLY_TABLE}")
    print(f"  device_summary:  {GOLD_DEVICE_TABLE}")
    print(f"  aqi_alerts:      {GOLD_AQI_TABLE}")
else:
    print(f"Mode: Legacy (abfss)")
    print(f"Silver input:   {SILVER_PATH}")
    print(f"Gold outputs:")
    print(f"  hourly_metrics:  {GOLD_HOURLY_PATH}")
    print(f"  device_summary:  {GOLD_DEVICE_PATH}")
    print(f"  aqi_alerts:      {GOLD_AQI_PATH}")

# COMMAND ----------

# Read Silver clean table
if USE_UC:
    df_silver = spark.table(SILVER_TABLE)
else:
    df_silver = spark.read.format("delta").load(SILVER_PATH)
print(f"Silver records: {df_silver.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Table 1: Hourly Metrics per Device
# MAGIC
# MAGIC Aggregates sensor readings into hourly averages. This is the core analytics
# MAGIC table — it answers "what was the average air quality for each device per hour?"

# COMMAND ----------

df_hourly = (
    df_silver
    .groupBy("device_id", "event_hour")
    .agg(
        # Pollution metrics — averages
        F.round(F.avg("temperature"), 2).alias("avg_temperature"),
        F.round(F.avg("humidity"), 2).alias("avg_humidity"),
        F.round(F.avg("pm25"), 2).alias("avg_pm25"),
        F.round(F.avg("no2"), 2).alias("avg_no2"),
        F.round(F.avg("co"), 2).alias("avg_co"),

        # Min/max for range analysis
        F.round(F.min("temperature"), 2).alias("min_temperature"),
        F.round(F.max("temperature"), 2).alias("max_temperature"),
        F.round(F.max("pm25"), 2).alias("max_pm25"),

        # Location (average — devices are roughly stationary)
        F.round(F.avg("latitude"), 6).alias("avg_latitude"),
        F.round(F.avg("longitude"), 6).alias("avg_longitude"),

        # Record count for confidence scoring
        F.count("*").alias("reading_count"),
    )
    .withColumn("_aggregated_at", F.current_timestamp())
    .orderBy("device_id", "event_hour")
)

# Write hourly metrics — MERGE to preserve historical data
def _write_or_merge(df, uc_table, adls_path, merge_keys):
    """Write a DataFrame using MERGE if the target exists, otherwise create it."""
    if USE_UC:
        if table_exists(uc_table):
            delta_t = DeltaTable.forName(spark, uc_table)
            merge_cond = " AND ".join(f"target.{k} = source.{k}" for k in merge_keys)
            delta_t.alias("target").merge(
                df.alias("source"), merge_cond
            ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
        else:
            df.write.format("delta").saveAsTable(uc_table)
    else:
        if path_exists(adls_path):
            delta_t = DeltaTable.forPath(spark, adls_path)
            merge_cond = " AND ".join(f"target.{k} = source.{k}" for k in merge_keys)
            delta_t.alias("target").merge(
                df.alias("source"), merge_cond
            ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
        else:
            df.write.format("delta").save(adls_path)

_write_or_merge(df_hourly, GOLD_HOURLY_TABLE, GOLD_HOURLY_PATH, ["device_id", "event_hour"])

print(f"✓ Hourly metrics: {df_hourly.count()} rows")
df_hourly.show(10, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Table 2: Device Summary
# MAGIC
# MAGIC One row per device with overall statistics. Useful for device health
# MAGIC monitoring and fleet management dashboards.

# COMMAND ----------

df_device_summary = (
    df_silver
    .groupBy("device_id")
    .agg(
        F.count("*").alias("total_readings"),
        F.min("event_timestamp").alias("first_reading_at"),
        F.max("event_timestamp").alias("last_reading_at"),

        # Average conditions
        F.round(F.avg("temperature"), 2).alias("avg_temperature"),
        F.round(F.avg("humidity"), 2).alias("avg_humidity"),
        F.round(F.avg("pm25"), 2).alias("avg_pm25"),
        F.round(F.avg("no2"), 2).alias("avg_no2"),
        F.round(F.avg("co"), 2).alias("avg_co"),

        # Worst readings (peak pollution)
        F.round(F.max("pm25"), 2).alias("peak_pm25"),
        F.round(F.max("no2"), 2).alias("peak_no2"),
        F.round(F.max("co"), 2).alias("peak_co"),

        # Location
        F.round(F.avg("latitude"), 6).alias("latitude"),
        F.round(F.avg("longitude"), 6).alias("longitude"),
    )
    .withColumn("_aggregated_at", F.current_timestamp())
)

# Write device summary — MERGE by device_id
_write_or_merge(df_device_summary, GOLD_DEVICE_TABLE, GOLD_DEVICE_PATH, ["device_id"])

print(f"✓ Device summary: {df_device_summary.count()} devices")
df_device_summary.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Table 3: AQI Alerts
# MAGIC
# MAGIC Identifies hours where air quality exceeded WHO guidelines.
# MAGIC
# MAGIC **WHO Air Quality Guidelines (simplified):**
# MAGIC - PM2.5: > 25 µg/m³ (24-hour mean) → Unhealthy
# MAGIC - NO2: > 25 ppb (annual mean) → Elevated
# MAGIC - CO: > 4 ppm (24-hour mean) → Warning

# COMMAND ----------

df_aqi_alerts = (
    df_hourly
    .withColumn("pm25_alert",
        F.when(F.col("avg_pm25") > 100, "HAZARDOUS")
         .when(F.col("avg_pm25") > 50, "UNHEALTHY")
         .when(F.col("avg_pm25") > 25, "MODERATE")
         .otherwise("GOOD")
    )
    .withColumn("no2_alert",
        F.when(F.col("avg_no2") > 100, "HAZARDOUS")
         .when(F.col("avg_no2") > 50, "UNHEALTHY")
         .when(F.col("avg_no2") > 25, "MODERATE")
         .otherwise("GOOD")
    )
    .withColumn("co_alert",
        F.when(F.col("avg_co") > 8, "HAZARDOUS")
         .when(F.col("avg_co") > 4, "UNHEALTHY")
         .when(F.col("avg_co") > 2, "MODERATE")
         .otherwise("GOOD")
    )
    # Flag any row with at least one non-GOOD alert
    .withColumn("has_alert",
        (F.col("pm25_alert") != "GOOD") |
        (F.col("no2_alert") != "GOOD") |
        (F.col("co_alert") != "GOOD")
    )
    .filter(F.col("has_alert"))
    .select(
        "device_id",
        "event_hour",
        "avg_pm25", "pm25_alert",
        "avg_no2", "no2_alert",
        "avg_co", "co_alert",
        "avg_latitude", "avg_longitude",
        "reading_count",
    )
    .withColumn("_alerted_at", F.current_timestamp())
)

# Write AQI alerts — MERGE by device_id + event_hour
if df_aqi_alerts.count() > 0:
    _write_or_merge(df_aqi_alerts, GOLD_AQI_TABLE, GOLD_AQI_PATH, ["device_id", "event_hour"])
    print(f"✓ AQI alerts: {df_aqi_alerts.count()} alert periods")
    df_aqi_alerts.show(10, truncate=False)
else:
    print("✓ No AQI alerts — all readings within safe limits")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pipeline Summary

# COMMAND ----------

# Final summary
print("=" * 60)
print("GOLD LAYER SUMMARY")
print("=" * 60)

if USE_UC:
    for name, table in [
        ("hourly_metrics", GOLD_HOURLY_TABLE),
        ("device_summary", GOLD_DEVICE_TABLE),
    ]:
        df = spark.table(table)
        print(f"\n{name} ({table}):")
        print(f"  Records: {df.count()}")
        print(f"  Columns: {df.columns}")

    try:
        df_alerts = spark.table(GOLD_AQI_TABLE)
        print(f"\naqi_alerts ({GOLD_AQI_TABLE}):")
        print(f"  Records: {df_alerts.count()}")
        print(f"  Columns: {df_alerts.columns}")
    except Exception:
        print(f"\naqi_alerts: No alerts generated")
else:
    for name, path in [
        ("hourly_metrics", GOLD_HOURLY_PATH),
        ("device_summary", GOLD_DEVICE_PATH),
    ]:
        df = spark.read.format("delta").load(path)
        print(f"\n{name}:")
        print(f"  Records: {df.count()}")
        print(f"  Columns: {df.columns}")

    try:
        df_alerts = spark.read.format("delta").load(GOLD_AQI_PATH)
        print(f"\naqi_alerts:")
        print(f"  Records: {df_alerts.count()}")
        print(f"  Columns: {df_alerts.columns}")
    except Exception:
        print(f"\naqi_alerts: No alerts generated")

print("\n" + "=" * 60)
print("✓ Gold layer complete! Tables are ready for analytics.")
print("=" * 60)
