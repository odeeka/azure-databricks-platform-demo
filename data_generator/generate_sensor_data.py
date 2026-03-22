"""
IoT Environmental Sensor Data Generator
========================================
Simulates IoT devices sending environmental sensor readings to Azure ADLS Gen2.

What it does:
  - Generates realistic-looking sensor data (temperature, humidity, PM2.5, NO2, CO)
  - Writes JSON files to the "raw" container in the dev ADLS Gen2 storage account
  - Simulates multiple devices across different geographic locations
  - Runs in a continuous loop or for a fixed number of batches

The generated data lands in:
  abfss://raw@<storage_account>.dfs.core.windows.net/sensors/YYYY/MM/DD/HH/

This is the entry point for the medallion pipeline:
  Raw JSON → Bronze (Delta) → Silver (cleaned) → Gold (aggregated)

Usage:
  # Set environment variables (or use .env file)
  export AZURE_STORAGE_ACCOUNT_NAME="stdbdemodeveus2"
  export AZURE_STORAGE_ACCOUNT_KEY="<your-key>"

  # Generate 5 batches of data (default)
  python generate_sensor_data.py

  # Generate data continuously every 10 seconds
  python generate_sensor_data.py --continuous --interval 10

  # Generate a specific number of batches
  python generate_sensor_data.py --batches 20

Requirements:
  pip install -r requirements.txt
"""

import argparse
import json
import os
import random
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from azure.storage.filedatalake import DataLakeServiceClient
from dotenv import load_dotenv

# Load .env file if present (for local development)
load_dotenv()

# =============================================================================
# Configuration
# =============================================================================

# Simulated device fleet — 5 devices across different locations
# Each device has a fixed location (lat/lon) and slight sensor bias
DEVICES = [
    {
        "device_id": "sensor-001",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "city": "New York",
        "temp_bias": 0.0,
        "humidity_bias": 5.0,
    },
    {
        "device_id": "sensor-002",
        "latitude": 34.0522,
        "longitude": -118.2437,
        "city": "Los Angeles",
        "temp_bias": 3.0,
        "humidity_bias": -10.0,
    },
    {
        "device_id": "sensor-003",
        "latitude": 41.8781,
        "longitude": -87.6298,
        "city": "Chicago",
        "temp_bias": -2.0,
        "humidity_bias": 0.0,
    },
    {
        "device_id": "sensor-004",
        "latitude": 47.6062,
        "longitude": -122.3321,
        "city": "Seattle",
        "temp_bias": -5.0,
        "humidity_bias": 15.0,
    },
    {
        "device_id": "sensor-005",
        "latitude": 29.7604,
        "longitude": -95.3698,
        "city": "Houston",
        "temp_bias": 5.0,
        "humidity_bias": 10.0,
    },
]


def generate_reading(device: dict, timestamp: datetime) -> dict:
    """
    Generate a single sensor reading for a device.

    Sensor ranges are realistic but simplified:
      - temperature: -10 to 45 °C (with device bias)
      - humidity: 20 to 95 % (with device bias)
      - pm25: 0 to 150 µg/m³ (PM2.5 particle concentration)
      - no2: 0 to 200 ppb (nitrogen dioxide)
      - co: 0 to 10 ppm (carbon monoxide)

    Occasionally injects anomalies (~5% chance) to make the data more
    interesting for the silver layer's data quality checks.
    """
    # Base readings with some randomness
    base_temp = 20.0 + device["temp_bias"] + random.gauss(0, 5)
    base_humidity = 60.0 + device["humidity_bias"] + random.gauss(0, 10)

    reading = {
        "event_id": str(uuid.uuid4()),
        "device_id": device["device_id"],
        "timestamp": timestamp.isoformat(),
        "temperature": round(base_temp, 2),
        "humidity": round(max(0, min(100, base_humidity)), 2),
        "pm25": round(max(0, random.gauss(35, 20)), 2),
        "no2": round(max(0, random.gauss(40, 25)), 2),
        "co": round(max(0, random.gauss(2, 1.5)), 2),
        "latitude": device["latitude"] + random.gauss(0, 0.001),  # GPS jitter
        "longitude": device["longitude"] + random.gauss(0, 0.001),
    }

    # ~5% chance of injecting an anomaly (null value, extreme reading, etc.)
    # This makes the silver layer's validation logic meaningful
    if random.random() < 0.05:
        anomaly_type = random.choice(["null_temp", "extreme_pm25", "negative_humidity"])
        if anomaly_type == "null_temp":
            reading["temperature"] = None
        elif anomaly_type == "extreme_pm25":
            reading["pm25"] = round(random.uniform(500, 1000), 2)
        elif anomaly_type == "negative_humidity":
            reading["humidity"] = round(random.uniform(-20, -1), 2)

    return reading


def generate_batch(num_readings_per_device: int = 3) -> list[dict]:
    """Generate a batch of readings for all devices."""
    now = datetime.now(timezone.utc)
    readings = []

    for device in DEVICES:
        for i in range(num_readings_per_device):
            # Spread readings within the current minute
            offset_seconds = random.randint(0, 59)
            ts = now.replace(second=offset_seconds, microsecond=random.randint(0, 999999))
            readings.append(generate_reading(device, ts))

    return readings


def get_adls_client() -> DataLakeServiceClient:
    """
    Create an ADLS Gen2 client using account name + key.

    In production, you'd use DefaultAzureCredential() or managed identity.
    For this demo, access keys keep things simple and explicit.
    """
    account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

    if not account_name or not account_key:
        print("ERROR: Set AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY")
        print("  You can get these from Terraform output:")
        print("    cd terraform/environments/dev")
        print('    terraform output storage_account_name')
        print('    terraform output -raw storage_account_key')
        sys.exit(1)

    return DataLakeServiceClient(
        account_url=f"https://{account_name}.dfs.core.windows.net",
        credential=account_key,
    )


def upload_to_adls(client: DataLakeServiceClient, readings: list[dict]) -> str:
    """
    Upload a batch of readings as a JSON file to the 'raw' container.

    File path pattern: sensors/YYYY/MM/DD/HH/batch_<uuid>.json
    This partitioning by date/hour makes it easy for Databricks Auto Loader
    to incrementally pick up new files.
    """
    now = datetime.now(timezone.utc)
    file_system_client = client.get_file_system_client("raw")

    # Partition path: year/month/day/hour
    partition_path = now.strftime("sensors/%Y/%m/%d/%H")
    file_name = f"batch_{uuid.uuid4().hex[:8]}.json"
    file_path = f"{partition_path}/{file_name}"

    # Write as newline-delimited JSON (NDJSON) — one record per line
    # This is the preferred format for Spark ingestion
    ndjson_content = "\n".join(json.dumps(r) for r in readings)

    file_client = file_system_client.get_file_client(file_path)
    file_client.upload_data(ndjson_content, overwrite=True)

    return file_path


def write_to_local(readings: list[dict], output_dir: str = "sample_data") -> str:
    """
    Write readings to a local file for testing without Azure credentials.
    Useful for local development and debugging the data format.
    """
    now = datetime.now(timezone.utc)
    partition_path = now.strftime("sensors/%Y/%m/%d/%H")
    dir_path = Path(output_dir) / partition_path
    dir_path.mkdir(parents=True, exist_ok=True)

    file_name = f"batch_{uuid.uuid4().hex[:8]}.json"
    file_path = dir_path / file_name

    ndjson_content = "\n".join(json.dumps(r) for r in readings)
    file_path.write_text(ndjson_content)

    return str(file_path)


def main():
    parser = argparse.ArgumentParser(
        description="Generate simulated IoT sensor data for the data platform demo"
    )
    parser.add_argument(
        "--batches",
        type=int,
        default=5,
        help="Number of batches to generate (default: 5)",
    )
    parser.add_argument(
        "--readings-per-device",
        type=int,
        default=3,
        help="Number of readings per device per batch (default: 3)",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuously (overrides --batches)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Seconds between batches in continuous mode (default: 30)",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Write to local filesystem instead of ADLS (for testing without Azure)",
    )
    args = parser.parse_args()

    # Validate Azure credentials unless running locally
    adls_client = None
    if not args.local_only:
        adls_client = get_adls_client()
        print(f"Connected to ADLS: {os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}")
    else:
        print("Running in local-only mode — files will be saved to ./sample_data/")

    print(f"Devices: {len(DEVICES)}")
    print(f"Readings per device per batch: {args.readings_per_device}")
    print(f"Total records per batch: {len(DEVICES) * args.readings_per_device}")
    print("---")

    batch_count = 0
    try:
        while True:
            batch_count += 1
            readings = generate_batch(args.readings_per_device)

            if args.local_only:
                file_path = write_to_local(readings)
                print(f"Batch {batch_count}: wrote {len(readings)} records → {file_path}")
            else:
                file_path = upload_to_adls(adls_client, readings)
                print(f"Batch {batch_count}: uploaded {len(readings)} records → raw/{file_path}")

            # Check if we should stop
            if not args.continuous and batch_count >= args.batches:
                break

            if args.continuous:
                print(f"  Next batch in {args.interval} seconds... (Ctrl+C to stop)")
                time.sleep(args.interval)

    except KeyboardInterrupt:
        print(f"\nStopped after {batch_count} batches.")

    print(f"\nDone! Generated {batch_count} batches total.")
    total_records = batch_count * len(DEVICES) * args.readings_per_device
    print(f"Total records: {total_records}")


if __name__ == "__main__":
    main()
