variable "resource_group_name" {
  description = "Name of the resource group for shared Unity Catalog resources"
  type        = string
}

variable "location" {
  description = "Azure region (must match the Databricks workspaces)"
  type        = string
}

variable "access_connector_name" {
  description = "Name of the Databricks Access Connector (managed identity)"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
