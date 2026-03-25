variable "environment" {
  description = "Environment name (e.g., dev, prod) — used as the catalog name"
  type        = string
}

variable "access_connector_id" {
  description = "Resource ID of the Azure Databricks Access Connector"
  type        = string
}

variable "access_connector_principal_id" {
  description = "Managed identity principal ID of the access connector (for role assignments)"
  type        = string
}

variable "data_lake_storage_account_name" {
  description = "Name of the environment's data lake storage account"
  type        = string
}

variable "data_lake_storage_account_id" {
  description = "Resource ID of the environment's data lake storage account (for role assignments)"
  type        = string
}

variable "workspace_users" {
  description = "List of users to add to the workspace with full access (demo-friendly)"
  type = list(object({
    user_name    = string
    display_name = string
    active       = bool
  }))
  default = []
}
