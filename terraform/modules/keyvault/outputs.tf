output "key_vault_id" {
  description = "Resource ID of the Key Vault"
  value       = azurerm_key_vault.this.id
}

output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.this.name
}

output "key_vault_uri" {
  description = "URI of the Key Vault (https://<name>.vault.azure.net/)"
  value       = azurerm_key_vault.this.vault_uri
}

output "storage_account_key_secret_name" {
  description = "Name of the Key Vault secret that holds the storage account key"
  value       = azurerm_key_vault_secret.storage_account_key.name
}
