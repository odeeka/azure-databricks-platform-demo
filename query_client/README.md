# Query Client — Access Gold Tables Locally

A lightweight Python CLI to query Databricks Unity Catalog **Gold tables** from
your local machine, without opening the Databricks workspace.

> **No token required!** If you are logged in via Azure CLI (`az login`), the
> script authenticates automatically — no Personal Access Token needed.

## Prerequisites

- Python 3.10+
- A running **SQL Warehouse** in your Databricks workspace
- One of: Personal Access Token, Azure CLI session, or Service Principal credentials

## Setup

```bash
cd query_client
pip install -r requirements.txt
```

## Quickstart (no token needed)

If you are already logged in via Azure CLI:

```bash
cd query_client
pip install -r requirements.txt

export DATABRICKS_HOST="adb-xxxx.azuredatabricks.net"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/<warehouse-id>"

python query_gold_tables.py
```

That's it — no token, no secrets. The script picks up your `az login` session
automatically.

## Authentication

The script tries these methods in order:

### 1. Azure CLI (recommended — zero secrets)

If `DATABRICKS_TOKEN` is **not** set, the script automatically authenticates
using your Azure CLI session (`az login`). This is the simplest and most secure
option — no tokens to generate, rotate, or store.

```bash
az login   # only needed once per session
export DATABRICKS_HOST="adb-xxxx.azuredatabricks.net"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/<warehouse-id>"
python query_gold_tables.py
```

This uses `DefaultAzureCredential` from the `azure-identity` package.

### 2. Environment Variables (Personal Access Token)

If Azure CLI is not available, you can use a Databricks Personal Access Token:

```bash
export DATABRICKS_HOST="adb-xxxx.azuredatabricks.net"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/<warehouse-id>"
export DATABRICKS_TOKEN="dapi..."
```

**Where to find these values:**

- **Host**: Databricks workspace URL (without `https://`)
- **HTTP path**: SQL Warehouses → select warehouse → Connection details → HTTP path
- **Token**: User Settings → Developer → Access tokens → Generate new token

**Note:** Some workspaces disable Personal Access Token generation. In that case, use Azure CLI authentication (method 1) instead.

### 3. Interactive Prompt

If neither method above works, the script will prompt you for host, HTTP path,
and token at runtime.

## Usage

### Query all Gold tables

```bash
python query_gold_tables.py
```

### Query a specific table

```bash
python query_gold_tables.py --table hourly    # dev.gold.hourly_metrics
python query_gold_tables.py --table device    # dev.gold.device_summary
python query_gold_tables.py --table aqi       # dev.gold.aqi_alerts
```

### Run a custom SQL query

```bash
python query_gold_tables.py --sql "SELECT device_id, avg_pm25 FROM dev.gold.hourly_metrics WHERE avg_pm25 > 50"
```

### Use a different catalog

```bash
python query_gold_tables.py --catalog prod
# or
export DATABRICKS_CATALOG="prod"
python query_gold_tables.py
```

## Example Output

```text
Connecting to adb-xxxx.azuredatabricks.net...
✓ Connected

============================================================
  Gold: Hourly Metrics
============================================================
device_id  | event_hour          | avg_temperature | avg_pm25 | avg_no2 | reading_count
-----------+---------------------+-----------------+----------+---------+--------------
sensor-001 | 2026-03-25 10:00:00 | 21.34           | 38.52    | 45.12   | 48
sensor-002 | 2026-03-25 10:00:00 | 18.90           | 29.10    | 33.78   | 50

(2 rows)

✓ Done
```

## Environment Variables Reference

| Variable | Required | Default | Description |
| - | - | - | - |
| `DATABRICKS_HOST` | Yes | - | Workspace hostname (no `https://`) |
| `DATABRICKS_HTTP_PATH` | Yes | - | SQL Warehouse HTTP path |
| `DATABRICKS_TOKEN` | No* | - | Personal Access Token or Service Principal token |
| `DATABRICKS_CATALOG` | No | `dev` | Unity Catalog name |
