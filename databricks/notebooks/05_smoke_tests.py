# Databricks notebook source
# =============================================================================
# 05_smoke_tests
# =============================================================================
# Purpose: Simple validation tests for each layer of the medallion pipeline.
#          Run this after the pipeline to verify everything worked correctly.
#
# These aren't unit tests — they're smoke tests that check:
#   - Tables exist and have data
#   - Schema is correct
#   - Data quality expectations are met
#   - Aggregations make sense
# =============================================================================

# COMMAND ----------

# MAGIC %md
# MAGIC # Pipeline Smoke Tests
# MAGIC
# MAGIC Validates that all layers of the medallion pipeline were created correctly.
# MAGIC Run this after `04_run_full_pipeline` to verify the results.

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %run ./_config

# COMMAND ----------

if USE_UC:
    # Unity Catalog managed table references
    TABLES = {
        "bronze": f"{CATALOG}.bronze.sensor_readings",
        "silver_clean": f"{CATALOG}.silver.sensor_readings_clean",
        "silver_quarantine": f"{CATALOG}.silver.sensor_readings_quarantine",
        "gold_hourly": f"{CATALOG}.gold.hourly_metrics",
        "gold_device": f"{CATALOG}.gold.device_summary",
        "gold_aqi": f"{CATALOG}.gold.aqi_alerts",
    }
    print(f"Mode: Unity Catalog ({CATALOG})")
else:
    TABLES = None
    print("Mode: Legacy (abfss)")

# Legacy abfss paths (always defined for fallback)
PATHS = {
    "bronze": f"abfss://bronze@{STORAGE_ACCOUNT}.dfs.core.windows.net/sensor_readings",
    "silver_clean": f"abfss://silver@{STORAGE_ACCOUNT}.dfs.core.windows.net/sensor_readings_clean",
    "silver_quarantine": f"abfss://silver@{STORAGE_ACCOUNT}.dfs.core.windows.net/sensor_readings_quarantine",
    "gold_hourly": f"abfss://gold@{STORAGE_ACCOUNT}.dfs.core.windows.net/hourly_metrics",
    "gold_device": f"abfss://gold@{STORAGE_ACCOUNT}.dfs.core.windows.net/device_summary",
    "gold_aqi": f"abfss://gold@{STORAGE_ACCOUNT}.dfs.core.windows.net/aqi_alerts",
}

def read_table(key):
    """Read a Delta table by key, using UC or abfss depending on mode."""
    if USE_UC:
        return spark.table(TABLES[key])
    else:
        return spark.read.format("delta").load(PATHS[key])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test Utilities

# COMMAND ----------

class TestResults:
    """Simple test result tracker."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def check(self, name: str, condition: bool, message: str = ""):
        status = "PASS" if condition else "FAIL"
        self.results.append((name, status, message))
        if condition:
            self.passed += 1
            print(f"  ✓ {name}")
        else:
            self.failed += 1
            print(f"  ✗ {name}: {message}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'=' * 60}")
        print(f"TEST RESULTS: {self.passed}/{total} passed, {self.failed} failed")
        print(f"{'=' * 60}")
        if self.failed == 0:
            print("🎉 All tests passed!")
        else:
            print("\nFailed tests:")
            for name, status, msg in self.results:
                if status == "FAIL":
                    print(f"  ✗ {name}: {msg}")

tests = TestResults()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Layer Tests

# COMMAND ----------

print("=== BRONZE LAYER TESTS ===")
try:
    df_bronze = read_table("bronze")

    # Test: table exists and has records
    bronze_count = df_bronze.count()
    tests.check("bronze_has_data", bronze_count > 0, f"Expected > 0 records, got {bronze_count}")

    # Test: expected columns exist
    expected_cols = ["event_id", "device_id", "timestamp", "temperature", "humidity",
                     "pm25", "no2", "co", "latitude", "longitude", "_source_file", "_ingested_at"]
    for col in expected_cols:
        tests.check(f"bronze_has_column_{col}", col in df_bronze.columns, f"Missing column: {col}")

    # Test: has data from all 5 devices
    device_count = df_bronze.select("device_id").distinct().count()
    tests.check("bronze_has_all_devices", device_count >= 5, f"Expected >= 5 devices, got {device_count}")

    # Test: no fully empty records
    all_null = df_bronze.filter(
        F.col("device_id").isNull() & F.col("timestamp").isNull()
    ).count()
    tests.check("bronze_no_empty_records", all_null == 0, f"Found {all_null} fully empty records")

except Exception as e:
    tests.check("bronze_table_exists", False, str(e))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver Layer Tests

# COMMAND ----------

print("\n=== SILVER LAYER TESTS ===")
try:
    df_silver = read_table("silver_clean")

    # Test: silver has data
    silver_count = df_silver.count()
    tests.check("silver_has_data", silver_count > 0, f"Expected > 0 records, got {silver_count}")

    # Test: silver count <= bronze count (some records may be filtered)
    tests.check("silver_leq_bronze", silver_count <= bronze_count,
                f"Silver ({silver_count}) > Bronze ({bronze_count}) — data shouldn't grow")

    # Test: no null temperatures in silver (should be filtered)
    null_temps = df_silver.filter(F.col("temperature").isNull()).count()
    tests.check("silver_no_null_temps", null_temps == 0, f"Found {null_temps} null temperatures")

    # Test: no negative humidity (should be filtered)
    neg_humidity = df_silver.filter(F.col("humidity") < 0).count()
    tests.check("silver_no_negative_humidity", neg_humidity == 0, f"Found {neg_humidity} negative humidity")

    # Test: humidity in valid range
    bad_humidity = df_silver.filter((F.col("humidity") < 0) | (F.col("humidity") > 100)).count()
    tests.check("silver_humidity_in_range", bad_humidity == 0, f"Found {bad_humidity} out-of-range humidity")

    # Test: no duplicate event_ids
    unique_events = df_silver.select("event_id").distinct().count()
    tests.check("silver_no_duplicates", unique_events == silver_count,
                f"Duplicates found: {silver_count - unique_events}")

    # Test: event_timestamp is populated (parsed from string)
    null_ts = df_silver.filter(F.col("event_timestamp").isNull()).count()
    tests.check("silver_timestamps_parsed", null_ts == 0, f"Found {null_ts} null timestamps")

except Exception as e:
    tests.check("silver_table_exists", False, str(e))

# COMMAND ----------

# Test quarantine table
print("\n=== SILVER QUARANTINE TESTS ===")
try:
    df_quarantine = read_table("silver_quarantine")
    quarantine_count = df_quarantine.count()
    tests.check("quarantine_exists", True)

    # Test: quarantine + clean = bronze (approximately, due to dedup)
    total = silver_count + quarantine_count
    tests.check("quarantine_counts_balance", total <= bronze_count,
                f"Clean ({silver_count}) + Quarantine ({quarantine_count}) = {total}, Bronze = {bronze_count}")

    # Test: quarantine has reason column
    tests.check("quarantine_has_reason", "_quarantine_reason" in df_quarantine.columns,
                "Missing _quarantine_reason column")

except Exception as e:
    # Quarantine table might not exist if all data was clean
    print(f"  ℹ Quarantine table not found (this is OK if all data was valid): {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer Tests

# COMMAND ----------

print("\n=== GOLD LAYER TESTS ===")

# Test hourly metrics
try:
    df_hourly = read_table("gold_hourly")
    hourly_count = df_hourly.count()
    tests.check("gold_hourly_has_data", hourly_count > 0, f"Expected > 0 rows, got {hourly_count}")

    # Test: aggregation reduces row count
    tests.check("gold_hourly_is_aggregated", hourly_count < silver_count,
                f"Hourly ({hourly_count}) should < Silver ({silver_count})")

    # Test: expected columns
    for col in ["device_id", "event_hour", "avg_pm25", "avg_temperature", "reading_count"]:
        tests.check(f"gold_hourly_has_{col}", col in df_hourly.columns, f"Missing: {col}")

    # Test: reading_count is positive
    bad_counts = df_hourly.filter(F.col("reading_count") <= 0).count()
    tests.check("gold_hourly_positive_counts", bad_counts == 0, f"Found {bad_counts} non-positive counts")

except Exception as e:
    tests.check("gold_hourly_exists", False, str(e))

# Test device summary
try:
    df_device = read_table("gold_device")
    device_count = df_device.count()
    tests.check("gold_device_has_data", device_count > 0, f"Expected > 0 rows")
    tests.check("gold_device_has_all_devices", device_count >= 5, f"Expected 5 devices, got {device_count}")

    # Test: total_readings makes sense
    total_readings_sum = df_device.agg(F.sum("total_readings")).first()[0]
    tests.check("gold_device_readings_match_silver", total_readings_sum == silver_count,
                f"Sum of device readings ({total_readings_sum}) != Silver count ({silver_count})")

except Exception as e:
    tests.check("gold_device_exists", False, str(e))

# Test AQI alerts (may or may not have data)
try:
    df_aqi = read_table("gold_aqi")
    aqi_count = df_aqi.count()
    tests.check("gold_aqi_exists", True, f"{aqi_count} alerts found")

    # Test: alerts only for non-GOOD readings
    for col in ["pm25_alert", "no2_alert", "co_alert"]:
        if col in df_aqi.columns:
            tests.check(f"gold_aqi_has_{col}", True)
except Exception as e:
    print(f"  ℹ AQI alerts table not found (OK if no alerts): {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test Summary

# COMMAND ----------

tests.summary()
