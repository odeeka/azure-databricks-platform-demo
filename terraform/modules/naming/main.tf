# =============================================================================
# Module: Naming — Shared region abbreviation lookup
# =============================================================================
# Purpose: Provides a consistent region_short code used across all modules and
#          environments. Centralizes the region lookup to avoid duplication.
#
# Usage:
#   module "naming" {
#     source   = "../../modules/naming"   # adjust path as needed
#     location = var.location
#   }
#   # Then reference: module.naming.region_short
# =============================================================================

locals {
  region_short_map = {
    "eastus"      = "eus"
    "eastus2"     = "eus2"
    "westus2"     = "wus2"
    "westeurope"  = "weu"
    "northeurope" = "neu"
    "centralus"   = "cus"
    "uksouth"     = "uks"
  }
}
