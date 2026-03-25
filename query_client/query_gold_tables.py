#!/usr/bin/env python3
"""
Query Databricks Gold Tables Locally
=====================================
Connect to a Databricks SQL Warehouse and query Unity Catalog Gold tables
from your local machine.

Authentication methods (in priority order):
  1. Environment variables: DATABRICKS_HOST + DATABRICKS_TOKEN
  2. Azure CLI: uses `az login` session (requires azure-identity)
  3. Interactive prompt: asks for host + token at runtime

Usage:
  python query_gold_tables.py                     # query all Gold tables
  python query_gold_tables.py --table hourly      # query hourly_metrics only
  python query_gold_tables.py --table device       # query device_summary only
  python query_gold_tables.py --table aqi          # query aqi_alerts only
  python query_gold_tables.py --sql "SELECT ..."   # run a custom SQL query
"""

import argparse
import os
import sys
from typing import Optional


def get_token_from_azure_cli() -> Optional[str]:
    """Attempt to get a Databricks token via Azure CLI / DefaultAzureCredential."""
    try:
        from azure.identity import DefaultAzureCredential

        credential = DefaultAzureCredential()
        # The Databricks resource ID for Azure
        token = credential.get_token(
            "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/.default"
        ).token
        return token
    except Exception:
        return None


def get_connection(host: str, http_path: str, token: str):
    """Create a Databricks SQL connection."""
    from databricks import sql

    return sql.connect(
        server_hostname=host,
        http_path=http_path,
        access_token=token,
    )


def resolve_credentials() -> tuple[str, str, str]:
    """
    Resolve Databricks host, HTTP path, and access token.

    Checks environment variables first, then Azure CLI, then prompts
    interactively.
    """
    host = os.environ.get("DATABRICKS_HOST", "")
    http_path = os.environ.get("DATABRICKS_HTTP_PATH", "")
    token = os.environ.get("DATABRICKS_TOKEN", "")

    # Try Azure CLI if no token set
    if not token:
        print("No DATABRICKS_TOKEN found, trying Azure CLI...")
        token = get_token_from_azure_cli() or ""
        if token:
            print("✓ Authenticated via Azure CLI")

    # Interactive fallback
    if not host:
        host = input("Databricks host (e.g. adb-xxxx.azuredatabricks.net): ").strip()
    if not http_path:
        http_path = input("SQL Warehouse HTTP path (e.g. /sql/1.0/warehouses/abc123): ").strip()
    if not token:
        token = input("Personal Access Token (dapi...): ").strip()

    if not all([host, http_path, token]):
        print("Error: host, http_path, and token are all required.")
        sys.exit(1)

    return host, http_path, token


# ---------------------------------------------------------------------------
# Gold table queries
# ---------------------------------------------------------------------------

CATALOG = os.environ.get("DATABRICKS_CATALOG", "dev")

QUERIES = {
    "hourly": f"""
        SELECT device_id, event_hour, avg_temperature, avg_humidity,
               avg_pm25, avg_no2, avg_co, reading_count
        FROM {CATALOG}.gold.hourly_metrics
        ORDER BY device_id, event_hour
    """,
    "device": f"""
        SELECT device_id, total_readings, first_reading_at, last_reading_at,
               avg_temperature, avg_pm25, peak_pm25, avg_no2, peak_no2
        FROM {CATALOG}.gold.device_summary
        ORDER BY device_id
    """,
    "aqi": f"""
        SELECT device_id, event_hour, avg_pm25, pm25_alert,
               avg_no2, no2_alert, avg_co, co_alert
        FROM {CATALOG}.gold.aqi_alerts
        ORDER BY event_hour, device_id
    """,
}


def run_query(cursor, sql: str, title: str = ""):
    """Execute a query and print results as a formatted table."""
    if title:
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}")

    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    if not rows:
        print("  (no results)")
        return

    # Calculate column widths
    col_widths = [len(c) for c in columns]
    str_rows = []
    for row in rows:
        str_row = [str(v) if v is not None else "NULL" for v in row]
        str_rows.append(str_row)
        for i, val in enumerate(str_row):
            col_widths[i] = max(col_widths[i], len(val))

    # Print header
    header = " | ".join(c.ljust(w) for c, w in zip(columns, col_widths))
    print(header)
    print("-+-".join("-" * w for w in col_widths))

    # Print rows
    for str_row in str_rows:
        print(" | ".join(v.ljust(w) for v, w in zip(str_row, col_widths)))

    print(f"\n({len(rows)} rows)")


def main():
    parser = argparse.ArgumentParser(
        description="Query Databricks Gold tables from your local machine."
    )
    parser.add_argument(
        "--table",
        choices=["hourly", "device", "aqi", "all"],
        default="all",
        help="Which Gold table to query (default: all)",
    )
    parser.add_argument(
        "--sql",
        type=str,
        default=None,
        help="Run a custom SQL query instead of the predefined ones",
    )
    parser.add_argument(
        "--catalog",
        type=str,
        default=None,
        help="Override catalog name (default: env DATABRICKS_CATALOG or 'dev')",
    )
    args = parser.parse_args()

    # Allow --catalog to override
    global CATALOG, QUERIES
    if args.catalog:
        CATALOG = args.catalog
        # Rebuild queries with new catalog
        QUERIES = {
            "hourly": f"SELECT * FROM {CATALOG}.gold.hourly_metrics ORDER BY device_id, event_hour",
            "device": f"SELECT * FROM {CATALOG}.gold.device_summary ORDER BY device_id",
            "aqi": f"SELECT * FROM {CATALOG}.gold.aqi_alerts ORDER BY event_hour, device_id",
        }

    host, http_path, token = resolve_credentials()

    print(f"\nConnecting to {host}...")
    conn = get_connection(host, http_path, token)
    cursor = conn.cursor()
    print("✓ Connected\n")

    try:
        if args.sql:
            run_query(cursor, args.sql, "Custom Query")
        elif args.table == "all":
            run_query(cursor, QUERIES["hourly"], "Gold: Hourly Metrics")
            run_query(cursor, QUERIES["device"], "Gold: Device Summary")
            run_query(cursor, QUERIES["aqi"], "Gold: AQI Alerts")
        else:
            titles = {
                "hourly": "Gold: Hourly Metrics",
                "device": "Gold: Device Summary",
                "aqi": "Gold: AQI Alerts",
            }
            run_query(cursor, QUERIES[args.table], titles[args.table])
    finally:
        cursor.close()
        conn.close()

    print("\n✓ Done")


if __name__ == "__main__":
    main()
