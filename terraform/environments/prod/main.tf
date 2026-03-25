# =============================================================================
# Prod Environment Configuration
# =============================================================================
# Purpose: Deploys the data platform for the prod environment.
#          Creates workspace + ADLS Gen2 storage. Unity Catalog is configured
#          separately in environments/unity-catalog/.
#
# Deployment order:
#   1. terraform -chdir=environments/shared apply       (shared Azure resources)
#   2. terraform -chdir=environments/dev apply           (dev workspace)
#   3. terraform -chdir=environments/prod apply          (this file)
#   4. terraform -chdir=environments/unity-catalog apply (metastore + catalogs)
#
# Usage:
#   cd terraform/environments/prod
#   terraform init
#   terraform plan -var-file=../../terraform.tfvars
#   terraform apply -var-file=../../terraform.tfvars
# =============================================================================


# ---------------------------------------------------------------------------
# Platform — workspace + storage
# ---------------------------------------------------------------------------
module "platform" {
  source = "../../modules/platform"

  environment    = "prod"
  location       = "westeurope"
  databricks_sku = "premium"

  # Auth passthrough
  tenant_id       = var.tenant_id
  subscription_id = var.subscription_id
  client_id       = var.client_id
  client_secret   = var.client_secret

  tags = {
    owner   = "data-engineering-team"
    purpose = "production"
  }

  # ---------------------------------------------------------------------------
  # Cluster Policy + Cluster + Pipeline Job — disabled by default
  # Uncomment the lines below to enable them.
  # ---------------------------------------------------------------------------

  # enable_cluster_policy        = true
  # cluster_policy_max_workers   = 2              # prod: stricter limits
  # cluster_policy_node_types    = ["Standard_DS3_v2"]
  # cluster_policy_spark_version = "15.4.x-scala2.12"

  # enable_cluster = false   # prod: no interactive cluster, use jobs only

  # enable_pipeline_job      = true
  # pipeline_notebook_path   = "/Repos/main/databricks/notebooks/04_run_full_pipeline"
  # pipeline_notebook_params = {
  #   storage_account_name = "stdbdemoprodweu"
  #   catalog_name         = "prod"
  #   use_unity_catalog    = "True"
  # }
  # pipeline_schedule_cron = "0 0 * * * ?"   # every hour
}
