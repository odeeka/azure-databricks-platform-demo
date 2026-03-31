
# ---------------------------------------------------------------------------
# Naming — uses shared naming module to avoid duplicating region lookups
# ---------------------------------------------------------------------------
module "naming" {
  source   = "../../modules/naming"
  location = var.location
}

locals {
  region_short = module.naming.region_short
}
