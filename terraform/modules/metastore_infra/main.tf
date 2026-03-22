# =============================================================================
# Module: Shared Infra — Access Connector for Unity Catalog
# =============================================================================
# Purpose: Creates the shared Azure infrastructure that Unity Catalog needs
#          to access storage via managed identity. Deployed ONCE per region.
#
# What gets created:
#   1. A dedicated resource group
#   2. A Databricks Access Connector (managed identity for storage access)
#
# Note: The metastore itself is auto-created by Azure when the first workspace
#       is provisioned. No storage account is needed here — each catalog
#       defines its own storage_root pointing to the environment's ADLS.
# =============================================================================

# Resource group to hold shared Unity Catalog infrastructure
resource "azurerm_resource_group" "metastore" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# Access Connector — provides a managed identity that Databricks uses to
# access storage accounts. No keys to manage or rotate.
resource "azurerm_databricks_access_connector" "metastore" {
  name                = var.access_connector_name
  resource_group_name = azurerm_resource_group.metastore.name
  location            = azurerm_resource_group.metastore.location

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}
