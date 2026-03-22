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
