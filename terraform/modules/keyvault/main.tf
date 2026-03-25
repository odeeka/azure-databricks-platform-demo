# =============================================================================
# Module: Azure Key Vault
# Purpose: Creates a Key Vault for the environment and stores the ADLS
#          storage account key as a secret. The Key Vault is used as the
#          authoritative secret store; Databricks secret scopes read from it.
#
# Design decisions:
#   - RBAC authorization is used (modern approach, no legacy access policies).
#   - The deploying service principal gets Key Vault Secrets Officer so it can
#     write secrets during Terraform apply.
#   - Soft-delete is enabled (Azure default, 90 days retention).
#   - Public network access is allowed for demo simplicity. In production,
#     restrict to a private endpoint or specific IP ranges.
# =============================================================================

# Current client identity — used to grant the deploying SP access to the KV.
data "azurerm_client_config" "current" {}

# -----------------------------------------------------------------------------
# Key Vault
# -----------------------------------------------------------------------------
resource "azurerm_key_vault" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  # Use Azure RBAC for authorization (recommended over access policies)
  enable_rbac_authorization = true

  # Soft-delete: Azure enforces this (90 days). Purge protection disabled
  # so we can easily destroy the demo environment.
  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  tags = var.tags
}

# -----------------------------------------------------------------------------
# RBAC: give the deploying service principal Secrets Officer on this KV.
# This allows Terraform to create/update/delete secrets.
# -----------------------------------------------------------------------------
resource "azurerm_role_assignment" "secrets_officer" {
  scope                = azurerm_key_vault.this.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = var.service_principal_object_id
}

# -----------------------------------------------------------------------------
# Secret: ADLS storage account primary access key
# This is the key the Python data generator and (fallback) Spark config use.
# The actual value comes from the storage module output.
# -----------------------------------------------------------------------------
resource "azurerm_key_vault_secret" "storage_account_key" {
  name         = "storage-account-key"
  value        = var.storage_account_key
  key_vault_id = azurerm_key_vault.this.id

  content_type = "text/plain"
  tags         = var.tags

  # The role assignment must exist before we can write secrets
  depends_on = [azurerm_role_assignment.secrets_officer]
}
