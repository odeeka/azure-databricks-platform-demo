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

# =============================================================================
# Cluster Policy — optional, disabled by default
# =============================================================================
variable "enable_cluster_policy" {
  description = "Whether to create a cluster policy for cost-controlled clusters"
  type        = bool
  default     = false
}

variable "cluster_policy_max_workers" {
  description = "Maximum number of worker nodes allowed by the policy"
  type        = number
  default     = 4
}

variable "cluster_policy_node_types" {
  description = "Allowed node types (Azure VM SKUs)"
  type        = list(string)
  default     = ["Standard_DS3_v2", "Standard_DS4_v2"]
}

variable "cluster_policy_spark_version" {
  description = "Fixed Spark version for the policy (null = not fixed)"
  type        = string
  default     = null
}

# =============================================================================
# Shared Cluster — optional, disabled by default
# =============================================================================
variable "enable_cluster" {
  description = "Whether to create a shared interactive cluster"
  type        = bool
  default     = false
}

variable "cluster_num_workers" {
  description = "Number of worker nodes for the shared cluster"
  type        = number
  default     = 1
}

variable "cluster_autotermination_minutes" {
  description = "Auto-terminate the cluster after this many idle minutes"
  type        = number
  default     = 30
}

# =============================================================================
# Pipeline Job — optional, disabled by default
# =============================================================================
variable "enable_pipeline_job" {
  description = "Whether to create a scheduled pipeline job"
  type        = bool
  default     = false
}

variable "pipeline_notebook_path" {
  description = "Workspace path to the orchestrator notebook"
  type        = string
  default     = "/Repos/main/databricks/notebooks/04_run_full_pipeline"
}

variable "pipeline_notebook_params" {
  description = "Parameters to pass to the pipeline notebook"
  type        = map(string)
  default     = {}
}

variable "pipeline_schedule_cron" {
  description = "Quartz cron expression for the pipeline schedule (null = no schedule)"
  type        = string
  default     = null
}
