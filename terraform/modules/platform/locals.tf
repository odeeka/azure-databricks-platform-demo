# -----------------------------------------------------------------------------
# Naming — uses shared naming module to avoid duplicating region lookups
# Pattern: {resource_prefix}-dbdemo-{environment}-{region_short}
# Example: rg-dbdemo-dev-eus2
# -----------------------------------------------------------------------------
module "naming" {
  source   = "../naming"
  location = var.location
}

locals {
  region_short = module.naming.region_short

  # Common tags applied to all resources
  common_tags = merge(var.tags, {
    environment = var.environment
    project     = "databricks-demo"
    managed_by  = "terraform"
  })

  # Naming convention pieces
  name_prefix = "dbdemo-${var.environment}-${local.region_short}"
}
