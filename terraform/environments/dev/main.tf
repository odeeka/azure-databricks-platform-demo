# =============================================================================
# Dev Environment Configuration
# =============================================================================
# Purpose: Deploys the data platform for the dev environment.
#          Creates workspace + ADLS Gen2 storage. Unity Catalog is configured
#          separately in environments/unity-catalog/.
#
# Deployment order:
#   1. terraform -chdir=environments/shared apply       (shared Azure resources)
#   2. terraform -chdir=environments/dev apply           (this file)
#   3. terraform -chdir=environments/prod apply          (prod workspace)
#   4. terraform -chdir=environments/unity-catalog apply (metastore + catalogs)
#
# Usage:
#   cd terraform/environments/dev
#   terraform init
#   terraform plan -var-file=../../terraform.tfvars
#   terraform apply -var-file=../../terraform.tfvars
# =============================================================================



# ---------------------------------------------------------------------------
# Platform — workspace + storage
# ---------------------------------------------------------------------------
module "platform" {
  source = "../../modules/platform"

  environment    = "dev"
  location       = "westeurope"
  databricks_sku = "premium"

  # Auth passthrough
  tenant_id       = var.tenant_id
  subscription_id = var.subscription_id
  client_id       = var.client_id
  client_secret   = var.client_secret

  tags = {
    owner   = "data-engineering-team"
    purpose = "demo"
  }
}

