# =============================================================================
# Module: Catalog — Per-Environment Unity Catalog Resources
# =============================================================================
# Purpose: Creates environment-specific Unity Catalog objects inside an
#          already-assigned metastore. Each environment (dev, prod) gets:

terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
    azurerm = {
      source = "hashicorp/azurerm"
    }
  }
}
#
#   1. Storage credential (using the shared access connector)
#   2. External location (pointing to the environment's ADLS storage)
#   3. Catalog (e.g., "dev" or "prod")
#   4. Schemas: bronze, silver, gold (matching the medallion architecture)
#
# This module uses the DATABRICKS provider (not azurerm) because these are
# Databricks-level resources, not Azure resources.
#
# Prerequisites:
#   - The metastore must already exist and be assigned to the workspace
#   - The databricks provider must be configured for a workspace in the metastore
# =============================================================================

# -----------------------------------------------------------------------------
# Storage Credential — tells Unity Catalog how to authenticate to ADLS
# Uses the Azure Databricks Access Connector's managed identity.
# No keys or secrets to manage!
# -----------------------------------------------------------------------------
resource "databricks_storage_credential" "this" {
  name         = "${var.environment}-storage-credential"

  azure_managed_identity {
    access_connector_id = var.access_connector_id
  }

  comment = "Managed identity credential for ${var.environment} environment data lake"
}

# Grant the storage credential to the account users (for demo simplicity)
resource "databricks_grants" "storage_credential" {
  storage_credential = databricks_storage_credential.this.id

  grant {
    principal  = "account users"
    privileges = ["ALL_PRIVILEGES"]
  }
}

# -----------------------------------------------------------------------------
# External Location — maps the environment's ADLS containers to Unity Catalog
# This lets notebooks reference data as catalog.schema.table instead of
# raw abfss:// paths.
# -----------------------------------------------------------------------------
# External Location: raw container — for reading ingested sensor data
resource "databricks_external_location" "raw" {
  name = "${var.environment}-raw"
  url  = "abfss://raw@${var.data_lake_storage_account_name}.dfs.core.windows.net/"

  credential_name = databricks_storage_credential.this.name
  comment         = "External location for ${var.environment} raw data lake"
  force_destroy   = true

  # Azure RBAC propagation can take 1-2 minutes — wait for the role assignment
  depends_on = [azurerm_role_assignment.data_lake_access]
}

# External Location: bronze container — for catalog managed tables
resource "databricks_external_location" "bronze" {
  name = "${var.environment}-bronze"
  url  = "abfss://bronze@${var.data_lake_storage_account_name}.dfs.core.windows.net/"

  credential_name = databricks_storage_credential.this.name
  comment         = "External location for ${var.environment} managed catalog tables"
  force_destroy   = true

  depends_on = [azurerm_role_assignment.data_lake_access]
}

resource "databricks_grants" "ext_loc_raw" {
  external_location = databricks_external_location.raw.id

  grant {
    principal  = "account users"
    privileges = ["ALL_PRIVILEGES"]
  }
}

resource "databricks_grants" "ext_loc_bronze" {
  external_location = databricks_external_location.bronze.id

  grant {
    principal  = "account users"
    privileges = ["ALL_PRIVILEGES"]
  }
}

# Grant access connector permission on the env data lake
# (so Unity Catalog can read/write via managed identity)
resource "azurerm_role_assignment" "data_lake_access" {
  scope                = var.data_lake_storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.access_connector_principal_id
}

# -----------------------------------------------------------------------------
# Catalog — one per environment (e.g., "dev", "prod")
# This is the top-level namespace: dev.bronze.sensor_readings
# -----------------------------------------------------------------------------
resource "databricks_catalog" "this" {
  name          = var.environment
  comment       = "Data catalog for the ${var.environment} environment"
  force_destroy = true

  # The auto-created Azure metastore uses "Default Storage" (no storage_root).
  # Each catalog needs an explicit managed location for its managed tables.
  # The path must be under an existing external location.
  storage_root = "abfss://bronze@${var.data_lake_storage_account_name}.dfs.core.windows.net/${var.environment}"

  depends_on = [databricks_external_location.bronze]
}

resource "databricks_grants" "catalog" {
  catalog = databricks_catalog.this.name

  grant {
    principal  = "account users"
    privileges = ["ALL_PRIVILEGES"]
  }
}

# -----------------------------------------------------------------------------
# Schemas — one per medallion layer
# Full table path: {env}.bronze.sensor_readings
#                   {env}.silver.sensor_readings_clean
#                   {env}.gold.hourly_metrics
# -----------------------------------------------------------------------------
resource "databricks_schema" "bronze" {
  catalog_name  = databricks_catalog.this.name
  name          = "bronze"
  comment       = "Bronze layer — raw ingested data"
  force_destroy = true
}

resource "databricks_schema" "silver" {
  catalog_name  = databricks_catalog.this.name
  name          = "silver"
  comment       = "Silver layer — cleaned and validated data"
  force_destroy = true
}

resource "databricks_schema" "gold" {
  catalog_name  = databricks_catalog.this.name
  name          = "gold"
  comment       = "Gold layer — aggregated analytics-ready data"
  force_destroy = true
}

# Grant schema access broadly (demo-friendly; production would be more restrictive)
resource "databricks_grants" "bronze_schema" {
  schema = databricks_schema.bronze.id

  grant {
    principal  = "account users"
    privileges = ["ALL_PRIVILEGES"]
  }
}

resource "databricks_grants" "silver_schema" {
  schema = databricks_schema.silver.id

  grant {
    principal  = "account users"
    privileges = ["ALL_PRIVILEGES"]
  }
}

resource "databricks_grants" "gold_schema" {
  schema = databricks_schema.gold.id

  grant {
    principal  = "account users"
    privileges = ["ALL_PRIVILEGES"]
  }
}

# -----------------------------------------------------------------------------
# Workspace Users — grant access to the workspace (demo-friendly)
# In production, use groups and more granular permissions.
# -----------------------------------------------------------------------------
resource "databricks_user" "workspace_users" {
  for_each = { for u in var.workspace_users : u.user_name => u }

  user_name    = each.value.user_name
  display_name = each.value.display_name
  active = each.value.active

  workspace_access       = true
  databricks_sql_access  = true
  allow_cluster_create   = true
  force                  = true  # Add even if user exists at account level
}
