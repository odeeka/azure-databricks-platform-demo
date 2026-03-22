# =============================================================================
# Outputs — Key information needed after deployment
# These values are used by the Python data generator and Databricks notebooks.
# =============================================================================

output "resource_group_name" {
  description = "Name of the resource group"
  value       = module.resource_group.name
}

output "storage_account_name" {
  description = "Name of the ADLS Gen2 storage account"
  value       = module.storage.name
}

output "storage_account_dfs_endpoint" {
  description = "ADLS Gen2 DFS endpoint (abfss:// compatible)"
  value       = module.storage.primary_dfs_endpoint
}

output "storage_account_key" {
  description = "Storage account primary access key (sensitive — use for local dev only)"
  value       = module.storage.primary_access_key
  sensitive   = true
}

output "storage_connection_string" {
  description = "Storage account connection string"
  value       = module.storage.primary_connection_string
  sensitive   = true
}

output "databricks_workspace_url" {
  description = "URL to access the Databricks workspace in a browser"
  value       = module.databricks.workspace_url
}

output "databricks_workspace_id" {
  description = "Databricks workspace unique ID"
  value       = module.databricks.workspace_id
}

output "environment" {
  description = "The environment this deployment represents"
  value       = var.environment
}

# Storage account ID — needed by unity-catalog environment for role assignments
output "storage_account_id" {
  description = "Resource ID of the ADLS Gen2 storage account"
  value       = module.storage.id
}
