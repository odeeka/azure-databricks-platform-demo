# =============================================================================
# Module: Platform — Per-Environment Infrastructure
# Purpose: Composes sub-modules to create the per-environment data platform.
#          Called from environments/dev or environments/prod.
#
# Architecture (4-step deployment):
#
#   Step 1: shared/           → Azure UC resources (storage, access connector)
#   Step 2: dev/              → Dev workspace + ADLS Gen2 (this module)
#   Step 3: prod/             → Prod workspace + ADLS Gen2 (this module)
#   Step 4: unity-catalog/    → Metastore + catalogs + schemas (both envs)
#
# This module creates:
#   - Resource Group
#   - ADLS Gen2 Storage Account (raw/bronze/silver/gold containers)
#   - Databricks Workspace (Premium SKU)
#
# Unity Catalog resources are created separately in environments/unity-catalog/
# =============================================================================

# Current client identity — passed to the Key Vault module for RBAC
data "azurerm_client_config" "current" {}

# =============================================================================
# Resource Group
# =============================================================================
module "resource_group" {
  source = "../resource_group"

  name     = "rg-${local.name_prefix}"
  location = var.location
  tags     = local.common_tags
}

# =============================================================================
# Storage Account (ADLS Gen2)
# Note: Storage account names must be globally unique, 3-24 chars, lowercase
#       alphanumeric only. We use a short suffix from the project name.
# =============================================================================
module "storage" {
  source = "../storage"

  # Remove hyphens and keep it short — storage names can't have special chars
  name                = "st${replace(local.name_prefix, "-", "")}"
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location
  tags                = local.common_tags
}

# =============================================================================
# Key Vault — stores the storage account key as a secret
# =============================================================================
module "keyvault" {
  source = "../keyvault"

  # KV names must be 3-24 chars, globally unique, alphanumeric + hyphens
  name                        = "kv-${local.name_prefix}"
  resource_group_name         = module.resource_group.name
  location                    = module.resource_group.location
  service_principal_object_id = data.azurerm_client_config.current.object_id
  storage_account_key         = module.storage.primary_access_key
  tags                        = local.common_tags
}

# =============================================================================
# Databricks Workspace
# =============================================================================
module "databricks" {
  source = "../databricks"

  name                = "dbw-${local.name_prefix}"
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location
  sku                 = var.databricks_sku
  tags                = local.common_tags
}
