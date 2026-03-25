# =============================================================================
# Provider requirements for the databricks module
# =============================================================================
# The databricks_* resources come from the "databricks/databricks" provider,
# NOT "hashicorp/databricks". This block tells Terraform where to find it.
# =============================================================================

terraform {
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = ">= 1.112.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.65"
    }
  }
}
