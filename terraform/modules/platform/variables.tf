# =============================================================================
# Input Variables for the Root Module
# These are the knobs you turn when deploying for dev vs. prod.
# =============================================================================

variable "environment" {
  description = "Environment name: dev or prod"
  type        = string

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be 'dev' or 'prod'."
  }
}

variable "location" {
  description = "Azure region to deploy all resources into"
  type        = string
  default     = "westeurope"
}

variable "databricks_sku" {
  description = "Databricks workspace SKU (premium recommended for Unity Catalog support)"
  type        = string
  default     = "premium"
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "subscription_id" {
  description = "Azure Subscription ID to deploy into"
  type        = string
  default     = ""
}

variable "tenant_id" {
  type = string
}

variable "client_id" {
  description = "Azure Client ID for service principal authentication"
  type        = string
}

variable "client_secret" {
  description = "Azure Client Secret for service principal authentication"
  type        = string
}
