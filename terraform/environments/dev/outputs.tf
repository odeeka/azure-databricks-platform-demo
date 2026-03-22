# =============================================================================
# Outputs
# =============================================================================

output "resource_group_name" {
  value = module.platform.resource_group_name
}

output "storage_account_name" {
  value = module.platform.storage_account_name
}

output "storage_account_id" {
  description = "Storage account resource ID (needed by unity-catalog env)"
  value       = module.platform.storage_account_id
}

output "storage_account_dfs_endpoint" {
  value = module.platform.storage_account_dfs_endpoint
}

output "storage_account_key" {
  value     = module.platform.storage_account_key
  sensitive = true
}

output "storage_connection_string" {
  value     = module.platform.storage_connection_string
  sensitive = true
}

output "databricks_workspace_url" {
  value = module.platform.databricks_workspace_url
}

output "databricks_workspace_id" {
  value = module.platform.databricks_workspace_id
}
