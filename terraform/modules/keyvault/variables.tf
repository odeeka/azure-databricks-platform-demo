variable "name" {
  description = "Name of the Key Vault (3-24 chars, globally unique)"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group to deploy the Key Vault into"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "service_principal_object_id" {
  description = "Object ID of the service principal that deploys Terraform — gets Key Vault Secrets Officer"
  type        = string
}

variable "storage_account_key" {
  description = "ADLS Gen2 storage account primary access key to store as a secret"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
