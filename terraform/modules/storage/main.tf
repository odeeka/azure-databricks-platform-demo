# =============================================================================
# Module: Storage Account (ADLS Gen2)
# Purpose: Creates an Azure Storage Account with Data Lake Storage Gen2 enabled.
#          This is the core storage layer for the data platform — raw data lands
#          here, and Databricks reads/writes bronze/silver/gold layers from it.
#
# Design decisions:
#   - HNS (hierarchical namespace) is enabled for ADLS Gen2 support.
#   - Standard_LRS replication is used — cheapest option, fine for a demo.
#   - Three containers are created: bronze, silver, gold (medallion architecture).
#   - A "raw" container is also created for the incoming sensor data.
# =============================================================================

resource "azurerm_storage_account" "this" {
  name                     = var.name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS" # Cheapest replication — sufficient for demo

  # Enable ADLS Gen2 (hierarchical namespace)
  is_hns_enabled = true

  # Optional: Network rules to restrict access (disabled by default)
  dynamic "network_rules" {
    for_each = var.network_rules_enabled ? [1] : []
    content {
      default_action             = var.network_rules_default_action
      ip_rules                   = var.network_rules_ip_rules
      virtual_network_subnet_ids = var.network_rules_subnet_ids
      bypass                     = ["AzureServices"]
    }
  }

  tags = var.tags
}

# -----------------------------------------------------------------------------
# Storage Containers — one per data layer in our medallion architecture
# "raw"    — landing zone for the Python data generator
# "bronze" — ingested data (minimal transformation, Delta format)
# "silver" — cleaned and validated data
# "gold"   — aggregated analytics-ready data
# -----------------------------------------------------------------------------

resource "azurerm_storage_container" "raw" {
  name                  = "raw"
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "bronze" {
  name                  = "bronze"
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "silver" {
  name                  = "silver"
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "gold" {
  name                  = "gold"
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}

# -----------------------------------------------------------------------------
# Lifecycle Policy — auto-delete old raw data to control storage costs
# Enabled by default for the "raw" container (90 days).
# Adjust retention_days or set lifecycle_policy_enabled = false to disable.
# -----------------------------------------------------------------------------
resource "azurerm_storage_management_policy" "lifecycle" {
  count              = var.lifecycle_policy_enabled ? 1 : 0
  storage_account_id = azurerm_storage_account.this.id

  rule {
    name    = "delete-old-raw-data"
    enabled = true

    filters {
      prefix_match = ["raw/"]
      blob_types   = ["blockBlob"]
    }

    actions {
      base_blob {
        delete_after_days_since_modification_greater_than = var.raw_data_retention_days
      }
    }
  }
}
