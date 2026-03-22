# =============================================================================
# Shared Environment — Access Connector for Unity Catalog
# =============================================================================
# Purpose: Deploys the SHARED Azure resources that Unity Catalog needs.
#          The Access Connector provides a managed identity used by
#          storage credentials in each environment's catalog.
#
# Note: The metastore is auto-created by Azure when the first workspace
#       is provisioned. No dedicated storage account is needed here.
#
# Deployment order:
#   1. terraform -chdir=environments/shared apply       (this file)
#   2. terraform -chdir=environments/dev apply
#   3. terraform -chdir=environments/prod apply
#   4. terraform -chdir=environments/unity-catalog apply
#
# Usage:
#   cd terraform/environments/shared
#   terraform init
#   terraform plan -var-file=../../terraform.tfvars
#   terraform apply -var-file=../../terraform.tfvars
# =============================================================================

module "metastore_infra" {
  source = "../../modules/metastore_infra"

  resource_group_name   = "rg-dbdemo-unity-${local.region_short}"
  location              = var.location
  access_connector_name = "ac-dbdemo-unity-${local.region_short}"
  tags                  = local.common_tags
}
