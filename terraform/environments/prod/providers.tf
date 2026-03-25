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

# Databricks provider — needed when cluster policy / cluster / job are enabled.
# Connects to the workspace created by this environment.
provider "databricks" {
  host = "https://${module.platform.databricks_workspace_url}"

  azure_client_id     = var.client_id
  azure_client_secret = var.client_secret
  azure_tenant_id     = var.tenant_id
}
