# =============================================================================
# Unity Catalog Environment — Catalogs + Schemas
# =============================================================================
# Purpose: Creates the Databricks Unity Catalog resources that span across
#          both dev and prod workspaces. Deployed AFTER both workspaces exist.
#
# Note:    Azure auto-creates & assigns a regional metastore when a workspace is
#          provisioned (limit: 1 per region per account). We look it up via a
#          data source instead of creating a new one.
#
# What it creates:
#   1. Dev catalog + bronze/silver/gold schemas + storage credential + external location
#   2. Prod catalog + bronze/silver/gold schemas + storage credential + external location
#
# Deployment order:
#   1. terraform -chdir=environments/shared apply       (shared Azure resources)
#   2. terraform -chdir=environments/dev apply           (dev workspace + storage)
#   3. terraform -chdir=environments/prod apply          (prod workspace + storage)
#   4. terraform -chdir=environments/unity-catalog apply (this file)
#
# Usage:
#   cd terraform/environments/unity-catalog
#   terraform init
#   terraform plan -var-file=../../terraform.tfvars
# =============================================================================

# =============================================================================
# Dev Catalog — storage credential, external location, catalog, schemas
# =============================================================================
module "dev_catalog" {

  source = "../../modules/catalog"

  environment = "dev"

  access_connector_id           = var.access_connector_id
  access_connector_principal_id = var.access_connector_principal_id

  data_lake_storage_account_name = var.dev_storage_account_name
  data_lake_storage_account_id   = var.dev_storage_account_id

  workspace_users = var.workspace_users
}

# =============================================================================
# Prod Catalog — storage credential, external location, catalog, schemas
# =============================================================================
module "prod_catalog" {

  source = "../../modules/catalog"

  environment = "prod"

  access_connector_id           = var.access_connector_id
  access_connector_principal_id = var.access_connector_principal_id

  data_lake_storage_account_name = var.prod_storage_account_name
  data_lake_storage_account_id   = var.prod_storage_account_id

  workspace_users = var.workspace_users
}

# =============================================================================
# Databricks Secret Scopes — per workspace
# Each workspace gets a "storage" scope with the ADLS access key stored as a
# secret. Notebooks read the key via dbutils.secrets.get() instead of
# hardcoding it in the notebook source.
#
# Flow: ADLS key → Key Vault secret (platform/dev|prod writes it)
#       → Databricks secret (unity-catalog reads KV → writes to Databricks)
# =============================================================================

# --- Read the storage key from the dev Key Vault ---
data "azurerm_key_vault" "dev" {
  name                = var.dev_key_vault_name
  resource_group_name = "rg-dbdemo-dev-weu"
}

data "azurerm_key_vault_secret" "dev_storage_key" {
  name         = "storage-account-key"
  key_vault_id = data.azurerm_key_vault.dev.id
}

# Dev workspace: secret scope + secret (default provider → dev workspace)
resource "databricks_secret_scope" "dev" {
  name = "storage"
}

resource "databricks_secret" "dev_storage_key" {
  scope        = databricks_secret_scope.dev.name
  key          = "account-key"
  string_value = data.azurerm_key_vault_secret.dev_storage_key.value
}

# --- Read the storage key from the prod Key Vault ---
data "azurerm_key_vault" "prod" {
  name                = var.prod_key_vault_name
  resource_group_name = "rg-dbdemo-prod-weu"
}

data "azurerm_key_vault_secret" "prod_storage_key" {
  name         = "storage-account-key"
  key_vault_id = data.azurerm_key_vault.prod.id
}

# Prod workspace: secret scope + secret (aliased provider → prod workspace)
resource "databricks_secret_scope" "prod" {
  provider = databricks.prod
  name     = "storage"
}

resource "databricks_secret" "prod_storage_key" {
  provider     = databricks.prod
  scope        = databricks_secret_scope.prod.name
  key          = "account-key"
  string_value = data.azurerm_key_vault_secret.prod_storage_key.value
}
