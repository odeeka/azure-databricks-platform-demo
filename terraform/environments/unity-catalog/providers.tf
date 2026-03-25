terraform {
  required_version = ">= 1.14.7"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.65"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.112.0"
    }
  }
}

# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------
provider "azurerm" {
  features {}
  tenant_id       = var.tenant_id
  subscription_id = var.subscription_id
  client_id       = var.client_id
  client_secret   = var.client_secret
}

# The Databricks provider connects to the dev workspace (any workspace in the
# region works — the metastore is regional, not workspace-specific).
# This is the default (unaliased) provider used by metastore resources and
# all catalog modules.
provider "databricks" {
  host  = "https://${var.dev_workspace_url}"

  azure_client_id     = var.client_id
  azure_client_secret = var.client_secret
  azure_tenant_id     = var.tenant_id
}

# Aliased provider for the prod workspace — used for prod-specific resources
# such as the secret scope that must live on the prod workspace.
provider "databricks" {
  alias = "prod"
  host  = "https://${var.prod_workspace_url}"

  azure_client_id     = var.client_id
  azure_client_secret = var.client_secret
  azure_tenant_id     = var.tenant_id
}