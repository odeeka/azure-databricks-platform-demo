variable "name" {
  description = "Name of the storage account (must be globally unique, 3-24 chars, lowercase alphanumeric only)"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.name))
    error_message = "Storage account name must be 3-24 characters, lowercase letters and numbers only."
  }
}

variable "resource_group_name" {
  description = "Name of the resource group to deploy into"
  type        = string
}

variable "location" {
  description = "Azure region for the storage account"
  type        = string
}

variable "tags" {
  description = "Tags to apply to the storage account"
  type        = map(string)
  default     = {}
}

# =============================================================================
# Network Rules — optional, disabled by default
# =============================================================================
variable "network_rules_enabled" {
  description = "Whether to enable storage account network rules (firewall)"
  type        = bool
  default     = false
}

variable "network_rules_default_action" {
  description = "Default action when no rule matches: Allow or Deny"
  type        = string
  default     = "Deny"
}

variable "network_rules_ip_rules" {
  description = "List of IP addresses or CIDR ranges allowed to access the storage account"
  type        = list(string)
  default     = []
}

variable "network_rules_subnet_ids" {
  description = "List of VNet subnet IDs allowed to access the storage account"
  type        = list(string)
  default     = []
}

# =============================================================================
# Lifecycle Policy — optional, enabled by default
# =============================================================================
variable "lifecycle_policy_enabled" {
  description = "Whether to enable lifecycle management for the raw container"
  type        = bool
  default     = true
}

variable "raw_data_retention_days" {
  description = "Days to retain raw data before auto-deletion (only when lifecycle_policy_enabled = true)"
  type        = number
  default     = 90
}
