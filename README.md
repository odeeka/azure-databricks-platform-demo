# Azure Databricks Data Platform Demo

A simple, demo-friendly data platform built with **Terraform** and **Azure Databricks**, implementing
the **medallion architecture** (Bronze → Silver → Gold) for IoT environmental sensor data.

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      SHARED (once per region)                                   │
│                                                                                 │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────────────┐ │
│  │ Unity Catalog Storage (ADLS) │  │ Databricks Access Connector              │ │
│  │ stdbdemounity<region>        │  │ ac-dbdemo-unity-<region>                 │ │
│  │ Container: metastore         │  │ (System-assigned managed identity)       │ │
│  └──────────────────────────────┘  └──────────────────────────────────────────┘ │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ Unity Catalog Metastore (one per region — shared by all workspaces)      │   │
│  │  ├── dev_catalog                                                         │   │
│  │  │    ├── bronze (schema)                                                │   │
│  │  │    ├── silver (schema)                                                │   │
│  │  │    └── gold   (schema)                                                │   │
│  │  └── prod_catalog                                                        │   │
│  │       ├── bronze (schema)                                                │   │
│  │       ├── silver (schema)                                                │   │
│  │       └── gold   (schema)                                                │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                     PER ENVIRONMENT (dev / prod)                             │
│                                                                              │
│  ┌─────────────────────────────┐    ┌─────────────────────────────────────┐  │
│  │  Azure Storage Account      │    │  Azure Databricks Workspace         │  │
│  │  (ADLS Gen2 enabled)        │    │  (Premium SKU)                      │  │
│  │                             │    │                                     │  │
│  │  Containers:                │    │  Notebooks:                         │  │
│  │  ┌───────┐                  │    │  ┌──────────────────────────────┐   │  │
│  │  │  raw  │ ◄── Python app   │    │  │ 00_setup_storage_access      │   │  │
│  │  └───────┘    writes JSON   │    │  │ 01_bronze_ingestion          │   │  │
│  │  ┌────────┐                 │    │  │ 02_silver_transformation     │   │  │
│  │  │ bronze │ ◄── Auto Loader │◄───┤  │ 03_gold_aggregation          │   │  │
│  │  └────────┘                 │    │  │ 04_run_full_pipeline         │   │  │
│  │  ┌────────┐                 │    │  │ 05_smoke_tests               │   │  │
│  │  │ silver │ ◄── Clean data  │    │  └──────────────────────────────┘   │  │
│  │  └────────┘                 │    │                                     │  │
│  │  ┌──────┐                   │    │  Cluster: Single-node               │  │
│  │  │ gold │ ◄── Aggregated    │    │  (auto-terminate after 20 min)      │  │
│  │  └──────┘                   │    │                                     │  │
│  └─────────────────────────────┘    └─────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow (Medallion Architecture)

```text
Raw JSON files          Bronze (Delta)           Silver (Delta)            Gold (Delta)
┌──────────────┐       ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│ IoT Sensor   │       │ Raw ingest   │        │ Cleaned &    │        │ Aggregated   │
│ readings     │──────▶│ + metadata   │───────▶│ validated    │───────▶│ analytics    │
│ (NDJSON)     │       │ + lineage    │        │ + deduped    │        │ tables       │
└──────────────┘       └──────────────┘        └──────────────┘        └──────────────┘
                       Auto Loader              Parse timestamps        Hourly metrics
                       Schema tracking          Range validation        Device summary
                       Append-only              Quarantine bad rows     AQI alerts
```

## Folder Structure

```text
azure-databricks-platform-demo/
├── README.md                              ← You are here
├── mise.toml                              ← Tool versions + task runner (replaces Makefile)
├── Makefile                               ← Legacy make targets (still works)
├── .github/
│   └── workflows/
│       ├── ci-validate.yml                ← PR validation (standalone)
│       ├── ci-validate-mise.yml           ← PR validation (mise-based — recommended)
│       ├── cd-deploy.yml                  ← Infra deployment (standalone)
│       ├── cd-deploy-mise.yml             ← Infra deployment (mise-based — recommended)
│       └── cd-sync-notebooks.yml          ← Sync notebooks to Databricks workspace
├── terraform/
│   ├── terraform.tfvars                   ← Credentials (gitignored)
│   ├── modules/
│   │   ├── platform/                      ← Per-env composition (workspace + storage)
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   └── locals.tf
│   │   ├── resource_group/                ← Azure Resource Group
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── storage/                       ← ADLS Gen2 Storage Account
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── databricks/                    ← Databricks Workspace
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── metastore_infra/               ← Shared UC Azure resources (ADLS, Access Connector)
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   └── catalog/                       ← Per-env UC config (credential, catalog, schemas)
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       └── outputs.tf
│   └── environments/
│       ├── shared/                        ← Step 1: → modules/metastore_infra
│       ├── dev/                           ← Step 2: → modules/platform
│       ├── prod/                          ← Step 3: → modules/platform
│       └── unity-catalog/                 ← Step 4: → modules/catalog (×2)
├── data_generator/
│   ├── generate_sensor_data.py            ← IoT sensor data simulator
│   ├── requirements.txt                   ← Python dependencies
│   └── .env.example                       ← Template for credentials
└── databricks/
    └── notebooks/
        ├── 00_setup_storage_access.py     ← Configure ADLS credentials + UC context
        ├── 01_bronze_ingestion.py         ← Raw JSON → Bronze (UC table or Delta path)
        ├── 02_silver_transformation.py    ← Clean & validate → Silver (UC or Delta)
        ├── 03_gold_aggregation.py         ← Aggregate → Gold (UC or Delta)
        ├── 04_run_full_pipeline.py        ← Orchestrate full run (passes UC widgets)
        └── 05_smoke_tests.py              ← Validate pipeline results (UC-aware)
```

## Prerequisites

- **Azure subscription** with permissions to create resources
- **Azure CLI** installed and authenticated (`az login`)
- **mise** installed (recommended) — manages Terraform + Python versions automatically
- **Terraform** >= 1.5 installed (or let mise install it)
- **Python** >= 3.10 installed (or let mise install it)
- **Git** for version control

### Quick Start with mise

```bash
# Install mise (one-time)
curl https://mise.run | sh

# Setup everything (installs tools, creates venv, inits Terraform)
mise run setup

# Run all validation checks locally (same as CI)
mise run validate

# See all available tasks
mise tasks
```

## Deployment Guide

### Step 1: Deploy Shared Infrastructure (Unity Catalog)

The shared layer creates the Azure resources needed for Unity Catalog's metastore.
This only needs to be deployed once per region.

```bash
cd terraform/environments/shared
terraform init
terraform plan
terraform apply

# Save outputs — needed by dev/prod
terraform output access_connector_id
terraform output access_connector_principal_id
terraform output metastore_storage_url
```

### Step 2: Deploy Infrastructure (Dev)

The dev environment creates the metastore object in Databricks and assigns it
to the workspace. It also creates the `dev` catalog with bronze/silver/gold schemas.

```bash
# Navigate to the dev environment
cd terraform/environments/dev

# Initialize Terraform (downloads providers)
terraform init

# Preview what will be created
terraform plan

# Deploy! (type "yes" when prompted)
terraform apply

# Save important outputs
terraform output storage_account_name
terraform output -raw storage_account_key    # Sensitive — don't share!
terraform output databricks_workspace_url
```

**Expected resources created:**

| Resource | Name Pattern | Purpose |
| - | - | - |
| Resource Group | `rg-dbdemo-dev-eus2` | Container for all dev resources |
| Storage Account | `stdbdemodeveus2` | ADLS Gen2 with raw/bronze/silver/gold containers |
| Databricks Workspace | `dbw-dbdemo-dev-eus2` | Compute and notebook environment |
| Unity Catalog Metastore | `metastore-dbdemo-<region>` | Shared metastore (created by first env) |
| Catalog | `dev` | Dev data catalog with bronze/silver/gold schemas |
| Storage Credential | `credential-dbdemo-<env>` | Managed identity access for external data |
| External Location | `ext-dbdemo-<env>-raw` | Maps ADLS `raw` container into UC |

### Step 3: Generate Sample Data

```bash
# Navigate to the data generator
cd data_generator

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Configure credentials (copy and edit the .env file)
cp .env.example .env
# Edit .env with your actual storage account name and key

# Generate 10 batches of sample data (75 records per batch)
python generate_sensor_data.py --batches 10

# Or test locally without Azure credentials
python generate_sensor_data.py --local-only --batches 5
```

**Expected output:**

```text
Connected to ADLS: stdbdemodeveus2
Devices: 5
Readings per device per batch: 3
Total records per batch: 15
---
Batch 1: uploaded 15 records → raw/sensors/2026/03/22/14/batch_a1b2c3d4.json
Batch 2: uploaded 15 records → raw/sensors/2026/03/22/14/batch_e5f6g7h8.json
...
Done! Generated 10 batches total.
Total records: 150
```

### Step 4: Run the Databricks Pipeline

1. **Open Databricks workspace:**

```bash
# Get the URLcd terraform/environments/dev
terraform output databricks_workspace_url
```

   Open the URL in your browser.

2. **Import the notebooks:**

- In Databricks, go to **Workspace** → **Users** → your username
- Click **Import** → select the files from `databricks/notebooks/`
- Or use the Databricks CLI:
  ```bash
  databricks workspace import_dir ./databricks/notebooks /Users/your@email.com/demo
  ```

3. **Create a cluster:**

   - Go to **Compute** → **Create Cluster**
   - Name: `demo-cluster`
   - Node type: `Standard_DS3_v2` (cheapest option)
   - Workers: `0` (single-node — cheapest for demos)
   - Auto-termination: `20 minutes`
   - Databricks Runtime: `14.x` or latest LTS

4. **Run the pipeline:**
   - Open `00_setup_storage_access` — update the storage account name and key, run all cells
   - Set `use_unity_catalog` widget to **yes** and enter your `catalog_name` (e.g., `dev`)
   - Open `04_run_full_pipeline` — run all cells (this calls Bronze → Silver → Gold)
   - Or run each notebook individually: `01` → `02` → `03`

5. **Validate results:**
   - Open `05_smoke_tests` — run all cells to verify all tables were created correctly

### Step 5: Deploy Unity Catalog

After both workspaces exist, deploy the shared Unity Catalog layer.
This creates the metastore, assigns it to both workspaces, and creates
catalogs + schemas for each environment.

```bash
cd terraform/environments/unity-catalog
terraform init
terraform plan -var-file=../../terraform.tfvars \
  -var="access_connector_id=$(terraform -chdir=../shared output -raw access_connector_id)" \
  -var="access_connector_principal_id=$(terraform -chdir=../shared output -raw access_connector_principal_id)" \
  -var="metastore_storage_url=$(terraform -chdir=../shared output -raw metastore_storage_url)" \
  -var="dev_workspace_url=$(terraform -chdir=../dev output -raw databricks_workspace_url)" \
  -var="dev_workspace_id=$(terraform -chdir=../dev output -raw databricks_workspace_id)" \
  -var="dev_storage_account_name=$(terraform -chdir=../dev output -raw storage_account_name)" \
  -var="dev_storage_account_id=$(terraform -chdir=../dev output -raw storage_account_id)" \
  -var="prod_workspace_url=$(terraform -chdir=../prod output -raw databricks_workspace_url)" \
  -var="prod_workspace_id=$(terraform -chdir=../prod output -raw databricks_workspace_id)" \
  -var="prod_storage_account_name=$(terraform -chdir=../prod output -raw storage_account_name)" \
  -var="prod_storage_account_id=$(terraform -chdir=../prod output -raw storage_account_id)"
terraform apply  # same -var flags as above
```

**Expected Unity Catalog resources:**
| Resource | Name | Purpose |
|----------|------|--------|
| Metastore | `metastore-dbdemo-weu` | Regional metastore shared by all workspaces |
| Catalog | `dev` | Dev data catalog (bronze/silver/gold schemas) |
| Catalog | `prod` | Prod data catalog (bronze/silver/gold schemas) |
| Storage Credential | `dev-storage-credential` | Managed identity access for dev data |
| Storage Credential | `prod-storage-credential` | Managed identity access for prod data |
| External Location | `dev-data-lake` | Maps dev ADLS `raw` container into UC |
| External Location | `prod-data-lake` | Maps prod ADLS `raw` container into UC |

## Validation Checklist

After running the pipeline, verify:

| Check | How to Verify | Expected |
|-------|--------------|----------|
| Raw data exists | List `raw` container in Storage Explorer | JSON files in `sensors/YYYY/MM/DD/HH/` |
| Bronze table created | `SELECT * FROM dev.bronze.sensor_readings` (UC) or read Delta from `bronze/sensor_readings` | Records with `_source_file`, `_ingested_at` |
| Silver clean table | `SELECT * FROM dev.silver.sensor_readings_clean` (UC) | No null temps, no negative humidity |
| Silver quarantine | `SELECT * FROM dev.silver.sensor_readings_quarantine` (UC) | Bad records with `_quarantine_reason` |
| Gold hourly metrics | `SELECT * FROM dev.gold.hourly_metrics` (UC) | Hourly averages per device |
| Gold device summary | `SELECT * FROM dev.gold.device_summary` (UC) | One row per device with stats |
| Gold AQI alerts | `SELECT * FROM dev.gold.aqi_alerts` (UC) | Hours exceeding WHO thresholds |
| Smoke tests pass | Run `05_smoke_tests` notebook | All checks green |

## Smoke Test Ideas per Layer

### Bronze
- ✅ Table has data (count > 0)
- ✅ All expected columns present
- ✅ Data from all 5 devices
- ✅ `_source_file` and `_ingested_at` populated

### Silver
- ✅ No null required fields (temperature, device_id, timestamp)
- ✅ No duplicate event_ids
- ✅ Humidity in range [0, 100]
- ✅ Timestamps properly parsed
- ✅ Record count ≤ Bronze (filtering, not growing)
- ✅ Quarantine table has reasons

### Gold
- ✅ Hourly metrics aggregated (fewer rows than Silver)
- ✅ All 5 devices in device summary
- ✅ `reading_count` > 0 for all hourly rows
- ✅ Sum of device `total_readings` = Silver count

## Cost Optimization Tips

| Strategy | Savings | How |
|----------|---------|-----|
| **Single-node cluster** | ~70% vs multi-node | Set workers to 0 |
| **Auto-terminate** | Variable | Set to 20 min idle timeout |
| **Standard_DS3_v2** | Cheapest viable | Use smallest node type |
| **LRS replication** | ~60% vs GRS | Already configured in Terraform |
| **Destroy when idle** | 100% | `terraform destroy` after demo |
| **Use `trial` SKU** | Free for 14 days | Change `databricks_sku = "trial"` |
| **Spot instances** | ~60-90% | Enable in cluster policy (not configured in demo) |

**Estimated cost for a 1-hour demo session:** ~$2-5 USD

**To destroy everything:**
```bash
cd terraform/environments/dev
terraform destroy    # Type "yes" to confirm
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Storage account key** (not managed identity) | Simplest auth for demo; production should use managed identity or service principal |
| **Public access** (not private endpoints) | Reduces complexity; production should use private networking |
| **Premium Databricks SKU** | Enables Unity Catalog, RBAC; `trial` is free for 14 days |
| **Local Terraform state** | Simple for solo dev; teams should use remote state in Azure Blob |
| **NDJSON format** | Simple, human-readable, native Spark support |
| **Delta tables** | ACID transactions, time travel, schema enforcement — Databricks standard |
| **Unity Catalog** | Centralized governance with per-env catalogs under a shared regional metastore |
| **Dual-mode notebooks** | Notebooks support both UC managed tables and legacy abfss:// paths via widget toggle |
| **Shared metastore pattern** | One metastore per region; dedicated `unity-catalog` env creates it after both workspaces exist |
| **Auto Loader** | Incremental file ingestion with checkpoints — production-ready pattern |

## Future Improvements

These are not implemented in this demo but would be natural next steps:

### Infrastructure
- [ ] **Remote Terraform state** — use Azure Blob backend for team collaboration
- [ ] **Private networking** — VNET injection for Databricks, private endpoints for storage
- [ ] **Managed identity** — replace storage keys with Azure Managed Identity
- [ ] **Key Vault** — store secrets in Azure Key Vault instead of notebook widgets
- [x] **CI/CD pipeline** — GitHub Actions (see `.github/workflows/`)

### Data Platform
- [x] **Unity Catalog** — centralized governance, fine-grained access control, data lineage
  - Per-environment catalogs (`dev`, `prod`) under a shared regional metastore
  - Managed tables in `catalog.schema.table` format with bronze/silver/gold schemas
  - Access Connector with managed identity for storage credential
- [ ] **Delta Live Tables (DLT)** — declarative pipeline framework (replaces manual notebook orchestration)
- [ ] **Databricks Workflows** — scheduled job orchestration with retries and alerting
- [ ] **Schema Registry** — formal schema management for the sensor data contract
- [ ] **Data quality framework** — Great Expectations or Databricks expectations for continuous monitoring
- [ ] **Streaming ingestion** — replace batch Auto Loader with continuous streaming mode

### Operations
- [ ] **Monitoring & alerting** — Azure Monitor, Databricks metrics, PagerDuty/Slack integration
- [ ] **Cost management** — Databricks cluster policies, spot instances, auto-scaling
- [ ] **Tagging strategy** — cost allocation tags, ownership tags
- [ ] **Disaster recovery** — GRS replication, cross-region Databricks workspace

### Security
- [ ] **Azure AD / Entra ID** — SSO for Databricks, RBAC for storage
- [ ] **Network security groups** — restrict inbound/outbound traffic
- [ ] **Encryption** — customer-managed keys for storage and Databricks
- [ ] **Audit logging** — Azure Activity Log, Databricks audit events

## CI/CD Pipelines (GitHub Actions)

Two sets of workflows are included — standalone and mise-based. Use whichever fits your team:

### Standalone Workflows (no mise dependency)

| Workflow | File | Trigger | What it does |
|----------|------|---------|--------------|
| **CI — Validate** | `ci-validate.yml` | Every PR and push to `main` | Terraform fmt/validate for dev+prod, Python linting with Ruff, data generator dry-run |
| **CD — Deploy** | `cd-deploy.yml` | Push to `main` (terraform changes) or manual | Terraform plan → apply for chosen environment; supports plan/apply/destroy |
| **CD — Sync Notebooks** | `cd-sync-notebooks.yml` | Push to `main` (notebook changes) or manual | Imports notebooks to Databricks `/Shared/demo-pipeline/` |

### mise-based Workflows (recommended)

| Workflow | File | Trigger | What it does |
|----------|------|---------|--------------|
| **CI — Validate (mise)** | `ci-validate-mise.yml` | Every PR and push to `main` | Same checks, but tool versions from `mise.toml` — local/CI parity guaranteed |
| **CD — Deploy (mise)** | `cd-deploy-mise.yml` | Push to `main` (terraform changes) or manual | Same plan/apply/destroy flow, tools managed by mise |

> **Why mise-based?** Tool versions are defined once in `mise.toml` and used everywhere —
> local dev, CI, and CD. No drift between "works on my machine" and CI failures.

### mise Task Reference

| Task | Command | Description |
|------|---------|-------------|
| `setup` | `mise run setup` | One-time: install tools, create venv, init Terraform |
| `validate` | `mise run validate` | Run all CI checks locally (Terraform + Python) |
| `validate:terraform` | `mise run validate:terraform` | Terraform fmt + validate for all environments |
| `validate:python` | `mise run validate:python` | Ruff lint + data generator dry-run |
| `fmt` | `mise run fmt` | Auto-format all Terraform and Python files |
| `plan` | `mise run plan` | Terraform plan (set `ENVIRONMENT=prod\|shared\|unity-catalog`) |
| `deploy` | `mise run deploy` | Terraform apply for dev/prod |
| `deploy:shared` | `mise run deploy:shared` | Deploy shared UC Azure resources (once) |
| `deploy:unity-catalog` | `mise run deploy:unity-catalog` | Deploy metastore + catalogs (requires shared + dev + prod) |
| `destroy` | `mise run destroy` | Terraform destroy |
| `generate` | `mise run generate` | Generate 10 batches of sensor data → ADLS |
| `generate:local` | `mise run generate:local` | Generate sample data locally (no Azure creds) |
| `generate:continuous` | `mise run generate:continuous` | Stream data every 15s (Ctrl+C to stop) |
| `demo` | `mise run demo` | Full walkthrough: shared → dev → prod → unity-catalog → generate |
| `outputs` | `mise run outputs` | Show Terraform outputs for current environment |
| `clean` | `mise run clean` | Remove temp files and caches |
| `clean:all` | `mise run clean:all` | Full reset (removes venv, .terraform) |
| `info` | `mise run info` | Show tool versions and project state |

Target a specific environment:
```bash
ENVIRONMENT=prod mise run plan
ENVIRONMENT=prod mise run deploy
```

### Setup Steps

1. **Create an Azure Service Principal:**
   ```bash
   az ad sp create-for-rbac --name "github-dbdemo" --role Contributor \
     --scopes /subscriptions/<YOUR_SUBSCRIPTION_ID>
   ```

2. **Add GitHub Repository Secrets** (Settings → Secrets → Actions):
   | Secret | Value |
   |--------|-------|
   | `AZURE_CLIENT_ID` | Service principal appId |
   | `AZURE_CLIENT_SECRET` | Service principal password |
   | `AZURE_SUBSCRIPTION_ID` | Your Azure subscription ID |
   | `AZURE_TENANT_ID` | Your Azure AD tenant ID |
   | `DATABRICKS_HOST` | Databricks workspace URL (e.g., `https://adb-123.12.azuredatabricks.net`) |
   | `DATABRICKS_TOKEN` | Databricks personal access token |

3. **(Optional) Configure GitHub Environments:**
   - Create `dev` and `prod` environments in Settings → Environments
   - Add **required reviewers** for the `prod` environment (manual approval gate)
   - This prevents accidental production deployments

### Manual Triggers

Both CD workflows support `workflow_dispatch` for manual runs:
- **Deploy**: choose environment (dev/prod) and action (plan/apply/destroy)
- **Sync Notebooks**: re-syncs all notebooks on demand

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `terraform init` fails | Check internet connectivity and that AzureRM provider is accessible |
| Storage account name taken | Names are globally unique — change the naming prefix in `main.tf` |
| Databricks workspace stuck creating | Can take 5-10 min; check Azure Portal for status |
| Data generator auth fails | Verify storage account name and key in `.env` |
| Auto Loader no files found | Ensure data generator ran and files are in `raw/sensors/` |
| Cluster won't start | Check Databricks workspace quotas; try a smaller node type |
| Notebooks can't access storage | Re-run `00_setup_storage_access` with correct credentials |
| Unity Catalog metastore already exists | Only one metastore per region — either import with `terraform import` or recreate |
| `CATALOG_DOES_NOT_EXIST` error | Ensure the unity-catalog environment deployed successfully; check `terraform -chdir=unity-catalog output` |
| Metastore not assigned to workspace | Run `terraform apply` in the unity-catalog env again — assignments may need workspaces to be fully ready |

## License

MIT — use freely for demos, learning, and as a starting point for your own platform.
