# ---------------------------------------------------------------------------
# Outputs — consumed by unity-catalog environment
# ---------------------------------------------------------------------------
output "access_connector_id" {
  description = "Resource ID of the Databricks Access Connector"
  value       = module.metastore_infra.access_connector_id
}

output "access_connector_principal_id" {
  description = "Managed identity principal ID of the access connector"
  value       = module.metastore_infra.access_connector_principal_id
}

output "resource_group_name" {
  description = "Resource group containing the shared resources"
  value       = module.metastore_infra.resource_group_name
}
