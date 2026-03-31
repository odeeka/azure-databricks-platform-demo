# =============================================================================
# Terragrunt — Root Configuration
# =============================================================================
# This file demonstrates how to adopt Terragrunt to eliminate duplication
# across the terraform/environments/ directory.
#
# Migration guide:
#   1. Install Terragrunt: brew install terragrunt (or curl https://terragrunt.io)
#   2. Place this file at terraform/terragrunt.hcl
#   3. Add per-environment terragrunt.hcl files (see examples below)
#   4. Run: cd terraform/environments/dev && terragrunt apply
#
# Benefits over raw Terraform:
#   - Single source of truth for provider config and backend
#   - DRY variables and outputs across dev/prod/shared
#   - Automatic dependency ordering between environments
#   - Consistent remote state configuration
#
# Directory structure after migration:
#   terraform/
#   ├── terragrunt.hcl                    ← this file (root config)
#   ├── modules/                          ← unchanged
#   └── environments/
#       ├── shared/terragrunt.hcl         ← includes root, sets inputs
#       ├── dev/terragrunt.hcl            ← includes root, depends on shared
#       ├── prod/terragrunt.hcl           ← includes root, depends on shared
#       └── unity-catalog/terragrunt.hcl  ← depends on dev + prod
# =============================================================================

# ---------------------------------------------------------------------------
# Remote state — all environments share the same backend storage account
# The state key is auto-derived from the relative path.
# ---------------------------------------------------------------------------
remote_state {
  backend = "azurerm"
  config = {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "stterraformstate"
    container_name       = "tfstate"
    key                  = "${path_relative_to_include()}/terraform.tfstate"
  }
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
}

# ---------------------------------------------------------------------------
# Generate provider block — shared across all child environments
# Individual environments can override or extend via their own terragrunt.hcl
# ---------------------------------------------------------------------------
generate "provider" {
  path      = "provider_generated.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<-EOF
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
    provider "azurerm" {
      features {}
    }
  EOF
}

# ---------------------------------------------------------------------------
# Common inputs — passed to all child modules automatically
# Override or extend in each environment's terragrunt.hcl
# ---------------------------------------------------------------------------
inputs = {
  location = "westeurope"
}

# =============================================================================
# EXAMPLE: environments/dev/terragrunt.hcl
# =============================================================================
# include "root" {
#   path = find_in_parent_folders()
# }
#
# dependency "shared" {
#   config_path = "../shared"
# }
#
# terraform {
#   source = "../../modules/platform"
# }
#
# inputs = {
#   environment    = "dev"
#   databricks_sku = "premium"
#   tenant_id      = get_env("ARM_TENANT_ID")
#   client_id      = get_env("ARM_CLIENT_ID")
#   client_secret  = get_env("ARM_CLIENT_SECRET")
#   subscription_id = get_env("ARM_SUBSCRIPTION_ID")
#   tags = {
#     owner   = "data-engineering-team"
#     purpose = "demo"
#   }
# }
# =============================================================================
