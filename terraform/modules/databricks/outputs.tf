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

# --- Optional cluster resources ---

output "cluster_policy_id" {
  description = "ID of the cluster policy (null if not enabled)"
  value       = var.enable_cluster_policy ? databricks_cluster_policy.this[0].id : null
}

output "cluster_id" {
  description = "ID of the shared cluster (null if not enabled)"
  value       = var.enable_cluster ? databricks_cluster.shared[0].id : null
}

output "pipeline_job_id" {
  description = "ID of the pipeline job (null if not enabled)"
  value       = var.enable_pipeline_job ? databricks_job.pipeline[0].id : null
}
