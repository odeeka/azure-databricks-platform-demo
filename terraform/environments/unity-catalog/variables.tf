# ---------------------------------------------------------------------------
# Variables — Unity Catalog Environment
# ---------------------------------------------------------------------------

# --- Service Principal Auth ---
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
  description = "Azure region (must match all workspaces)"
  type        = string
  default     = "westeurope"
}

# --- From shared environment: terraform -chdir=../shared output ---
variable "access_connector_id" {
  description = "From shared: terraform output -raw access_connector_id"
  type        = string
  default     = "/subscriptions/70dfe42b-7bb7-418d-bcef-0c66090f0ec3/resourceGroups/rg-dbdemo-unity-weu/providers/Microsoft.Databricks/accessConnectors/ac-dbdemo-unity-weu"
}

variable "access_connector_principal_id" {
  description = "From shared: terraform output -raw access_connector_principal_id"
  type        = string
  default     = "3b5fa6b1-a78b-4ae3-af3a-8ad56143a826"
}

# --- From dev environment: terraform -chdir=../dev output ---
variable "dev_workspace_url" {
  description = "From dev: terraform output -raw databricks_workspace_url"
  type        = string
  default     = "adb-7405611369112207.7.azuredatabricks.net"
}

variable "dev_workspace_id" {
  description = "From dev: terraform output -raw databricks_workspace_id"
  type        = string
  default     = "7405611369112207"
}

variable "dev_storage_account_name" {
  description = "From dev: terraform output -raw storage_account_name"
  type        = string
  default     = "stdbdemodevweu"
}

variable "dev_storage_account_id" {
  description = "From dev: terraform output -raw storage_account_id"
  type        = string
  default     = "/subscriptions/70dfe42b-7bb7-418d-bcef-0c66090f0ec3/resourceGroups/rg-dbdemo-dev-weu/providers/Microsoft.Storage/storageAccounts/stdbdemodevweu"
}

# --- From prod environment: terraform -chdir=../prod output ---
variable "prod_workspace_url" {
  description = "From prod: terraform output -raw databricks_workspace_url"
  type        = string
  default     = "adb-7405611258151482.2.azuredatabricks.net"
}

variable "prod_workspace_id" {
  description = "From prod: terraform output -raw databricks_workspace_id"
  type        = string
  default     = "7405611258151482"
}

variable "prod_storage_account_name" {
  description = "From prod: terraform output -raw storage_account_name"
  type        = string
  default     = "stdbdemoprodweu"
}

variable "prod_storage_account_id" {
  description = "From prod: terraform output -raw storage_account_id"
  type        = string
  default     = "/subscriptions/70dfe42b-7bb7-418d-bcef-0c66090f0ec3/resourceGroups/rg-dbdemo-prod-weu/providers/Microsoft.Storage/storageAccounts/stdbdemoprodweu"
}

# --- Key Vault names (from dev/prod environment outputs) ---
variable "dev_key_vault_name" {
  description = "From dev: terraform output -raw key_vault_name"
  type        = string
  default     = "kv-dbdemo-dev-weu"
}

variable "prod_key_vault_name" {
  description = "From prod: terraform output -raw key_vault_name"
  type        = string
  default     = "kv-dbdemo-prod-weu"
}

# --- Workspace Users ---
variable "workspace_users" {
  description = "Users to add to both dev and prod workspaces"
  type = list(object({
    user_name    = string
    display_name = string
    active = bool
  }))
  default = [
    {
      user_name    = "ptibor@live.com"
      display_name = "Tibor Petroczy"
      active       = true
    }
  ]
}
