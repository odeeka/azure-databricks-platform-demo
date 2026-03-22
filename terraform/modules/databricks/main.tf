# =============================================================================
# Module: Databricks Workspace
# Purpose: Creates an Azure Databricks workspace.
#
# Design decisions:
#   - Uses the "premium" SKU to enable features like Unity Catalog and RBAC.
#     The "standard" tier would also work for basic demos but limits features.
#   - No custom VNET injection — uses Databricks-managed networking for simplicity.
#     In production, you'd typically inject into a private VNET.
#   - No private endpoints — public access is allowed for demo simplicity.
#   - The managed resource group is auto-created by Databricks (contains worker
#     VMs, disks, NSGs etc.) and named with a "-managed" suffix.
# =============================================================================

resource "azurerm_databricks_workspace" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku

  # Databricks creates its own managed resource group for infrastructure.
  # We give it a predictable name so it's easy to identify.
  managed_resource_group_name = "${var.name}-managed-rg"

  tags = var.tags
}
