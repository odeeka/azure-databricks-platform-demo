variable "name" {
  description = "Name of the Databricks workspace"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group to deploy into"
  type        = string
}

variable "location" {
  description = "Azure region for the Databricks workspace"
  type        = string
}

variable "sku" {
  description = "Databricks workspace SKU: standard, premium, or trial"
  type        = string
  default     = "premium"

  validation {
    condition     = contains(["standard", "premium", "trial"], var.sku)
    error_message = "SKU must be one of: standard, premium, trial."
  }
}

variable "tags" {
  description = "Tags to apply to the Databricks workspace"
  type        = map(string)
  default     = {}
}

# =============================================================================
# VNet Injection — optional, disabled by default
# When enabled, Databricks workers run inside your own Azure VNet for
# network isolation. Requires pre-created VNet, subnets, and NSG associations.
# =============================================================================
variable "vnet_id" {
  description = "VNet ID for Databricks workspace VNet injection (null = Databricks-managed networking)"
  type        = string
  default     = null
}

variable "public_subnet_name" {
  description = "Name of the public (host) subnet for Databricks VNet injection"
  type        = string
  default     = ""
}

variable "private_subnet_name" {
  description = "Name of the private (container) subnet for Databricks VNet injection"
  type        = string
  default     = ""
}

variable "public_subnet_nsg_association_id" {
  description = "NSG association ID for the public subnet"
  type        = string
  default     = null
}

variable "private_subnet_nsg_association_id" {
  description = "NSG association ID for the private subnet"
  type        = string
  default     = null
}

variable "no_public_ip" {
  description = "Whether to disable public IPs for Databricks worker VMs (Secure Cluster Connectivity)"
  type        = bool
  default     = false
}

# =============================================================================
# Cluster Policy — optional, disabled by default
# =============================================================================
variable "enable_cluster_policy" {
  description = "Whether to create a cluster policy for cost-controlled clusters"
  type        = bool
  default     = false
}

variable "cluster_policy_name" {
  description = "Name of the cluster policy"
  type        = string
  default     = "Cost Controlled"
}

variable "cluster_policy_max_workers" {
  description = "Maximum number of worker nodes allowed by the policy"
  type        = number
  default     = 4
}

variable "cluster_policy_autotermination_max" {
  description = "Maximum auto-termination in minutes allowed by the policy"
  type        = number
  default     = 60
}

variable "cluster_policy_autotermination_default" {
  description = "Default auto-termination in minutes"
  type        = number
  default     = 30
}

variable "cluster_policy_node_types" {
  description = "Allowed node types (Azure VM SKUs)"
  type        = list(string)
  default     = ["Standard_DS3_v2", "Standard_DS4_v2"]
}

variable "cluster_policy_default_node_type" {
  description = "Default node type for clusters using this policy"
  type        = string
  default     = "Standard_DS3_v2"
}

variable "cluster_policy_spark_version" {
  description = "Fixed Spark version for the policy (null = not fixed)"
  type        = string
  default     = null
}

variable "cluster_policy_spot_instances" {
  description = "Whether to force spot/preemptible instances"
  type        = bool
  default     = true
}

# =============================================================================
# Shared Cluster — optional, disabled by default
# =============================================================================
variable "enable_cluster" {
  description = "Whether to create a shared interactive cluster"
  type        = bool
  default     = false
}

variable "cluster_name" {
  description = "Name of the shared cluster"
  type        = string
  default     = "shared-cluster"
}

variable "cluster_num_workers" {
  description = "Number of worker nodes for the shared cluster"
  type        = number
  default     = 1
}

variable "cluster_node_type" {
  description = "VM type for the shared cluster"
  type        = string
  default     = "Standard_DS3_v2"
}

variable "cluster_spark_version" {
  description = "Spark runtime version for the shared cluster"
  type        = string
  default     = "15.4.x-scala2.12"
}

variable "cluster_autotermination_minutes" {
  description = "Auto-terminate the cluster after this many idle minutes"
  type        = number
  default     = 30
}

variable "cluster_spark_conf" {
  description = "Additional Spark configuration key-value pairs"
  type        = map(string)
  default     = {}
}

# =============================================================================
# Pipeline Job — optional, disabled by default
# =============================================================================
variable "enable_pipeline_job" {
  description = "Whether to create a scheduled pipeline job"
  type        = bool
  default     = false
}

variable "pipeline_job_name" {
  description = "Name of the pipeline job"
  type        = string
  default     = "sensor-pipeline"
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

variable "pipeline_schedule_timezone" {
  description = "Timezone for the pipeline schedule"
  type        = string
  default     = "Europe/Budapest"
}

variable "pipeline_job_node_type" {
  description = "VM type for the pipeline job cluster"
  type        = string
  default     = "Standard_DS3_v2"
}

variable "pipeline_job_num_workers" {
  description = "Number of workers for the pipeline job cluster"
  type        = number
  default     = 1
}
