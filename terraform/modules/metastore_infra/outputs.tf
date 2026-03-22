output "access_connector_id" {
  description = "Resource ID of the Databricks Access Connector"
  value       = azurerm_databricks_access_connector.metastore.id
}

output "access_connector_principal_id" {
  description = "Managed identity principal ID of the access connector"
  value       = azurerm_databricks_access_connector.metastore.identity[0].principal_id
}

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.metastore.name
}
