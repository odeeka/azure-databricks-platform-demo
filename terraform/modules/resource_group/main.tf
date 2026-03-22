# =============================================================================
# Module: Resource Group
# Purpose: Creates an Azure Resource Group for a given environment.
#          Each environment (dev, prod) gets its own resource group to keep
#          resources isolated and easy to manage/delete.
# =============================================================================

resource "azurerm_resource_group" "this" {
  name     = var.name
  location = var.location

  tags = var.tags
}
