output "id" {
  description = "The ID of the Databricks workspace"
  value       = azurerm_databricks_workspace.this.id
}

output "workspace_url" {
  description = "The URL of the Databricks workspace (for browser access)"
  value       = azurerm_databricks_workspace.this.workspace_url
}

output "workspace_id" {
  description = "The unique identifier of the Databricks workspace"
  value       = azurerm_databricks_workspace.this.workspace_id
}

output "name" {
  description = "The name of the Databricks workspace"
  value       = azurerm_databricks_workspace.this.name
}
