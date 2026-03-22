# -----------------------------------------------------------------------------
# Local values — computed naming conventions
# Pattern: {resource_prefix}-dbdemo-{environment}-{region_short}
# Example: rg-dbdemo-dev-eus2
# -----------------------------------------------------------------------------
locals {
  # Short region code for naming (keeps names compact)
  region_short = lookup({
    "eastus"      = "eus"
    "eastus2"     = "eus2"
    "westus2"     = "wus2"
    "westeurope"  = "weu"
    "northeurope" = "neu"
    "centralus"   = "cus"
    "uksouth"     = "uks"
  }, var.location, replace(var.location, "/[aeiou]/", ""))

  # Common tags applied to all resources
  common_tags = merge(var.tags, {
    environment = var.environment
    project     = "databricks-demo"
    managed_by  = "terraform"
  })

  # Naming convention pieces
  name_prefix = "dbdemo-${var.environment}-${local.region_short}"
}
