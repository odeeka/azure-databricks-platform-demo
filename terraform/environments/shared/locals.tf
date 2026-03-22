
# ---------------------------------------------------------------------------
# Naming
# ---------------------------------------------------------------------------
locals {
  region_short = lookup({
    "eastus"      = "eus"
    "eastus2"     = "eus2"
    "westus2"     = "wus2"
    "westeurope"  = "weu"
    "northeurope" = "neu"
    "centralus"   = "cus"
    "uksouth"     = "uks"
  }, var.location, replace(var.location, "/[aeiou]/", ""))

  common_tags = {
    project    = "databricks-demo"
    managed_by = "terraform"
    layer      = "shared"
  }
}
