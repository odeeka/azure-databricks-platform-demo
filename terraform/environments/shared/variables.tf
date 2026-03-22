# ---------------------------------------------------------------------------
# Variables — same auth pattern as environments
# ---------------------------------------------------------------------------
variable "tenant_id" {
  type = string
}

variable "subscription_id" {
  type    = string
  default = ""
}

variable "client_id" {
  type = string
}

variable "client_secret" {
  type = string
}

variable "location" {
  description = "Azure region (must match the Databricks workspaces)"
  type        = string
  default     = "westeurope"
}
