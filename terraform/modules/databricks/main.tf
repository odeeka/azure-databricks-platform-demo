# =============================================================================
# Module: Databricks Workspace + Optional Cluster Resources
# Purpose: Creates an Azure Databricks workspace, and optionally:
#          - A cluster policy (cost controls)
#          - A shared interactive cluster
#          - A scheduled pipeline job
#
# All optional resources are disabled by default (enable_* = false).
# Enable them per-environment in the calling module.
#
# Design decisions:
#   - Uses the "premium" SKU to enable features like Unity Catalog and RBAC.
#     The "standard" tier would also work for basic demos but limits features.
#   - No custom VNET injection — uses Databricks-managed networking for simplicity.
#     In production, you'd typically inject into a private VNET.
#   - No private endpoints — public access is allowed for demo simplicity.
#   - The managed resource group is auto-created by Databricks (contains worker
#     VMs, disks, NSGs etc.) and named with a "-managed" suffix.
# =============================================================================

resource "azurerm_databricks_workspace" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku

  # Databricks creates its own managed resource group for infrastructure.
  # We give it a predictable name so it's easy to identify.
  managed_resource_group_name = "${var.name}-managed-rg"

  tags = var.tags
}

# =============================================================================
# Cluster Policy — Cost Controls (optional)
# =============================================================================
# Restricts what cluster configurations developers can create.
# Prevents runaway costs by limiting node count, VM type, and idle time.
# =============================================================================

resource "databricks_cluster_policy" "this" {
  count = var.enable_cluster_policy ? 1 : 0

  name = var.cluster_policy_name

  definition = jsonencode(merge(
    # Worker count — bounded range
    {
      "num_workers" = {
        "type"         = "range"
        "maxValue"     = var.cluster_policy_max_workers
        "defaultValue" = 1
      }
    },
    # Auto-termination — mandatory, bounded range
    {
      "autotermination_minutes" = {
        "type"         = "range"
        "minValue"     = 10
        "maxValue"     = var.cluster_policy_autotermination_max
        "defaultValue" = var.cluster_policy_autotermination_default
      }
    },
    # Node type allowlist
    {
      "node_type_id" = {
        "type"         = "allowlist"
        "values"       = var.cluster_policy_node_types
        "defaultValue" = var.cluster_policy_default_node_type
      }
    },
    # Spot instances (cost savings)
    var.cluster_policy_spot_instances ? {
      "azure_attributes.availability" = {
        "type"  = "fixed"
        "value" = "SPOT_WITH_FALLBACK_AZURE"
      }
    } : {},
    # Fixed Spark version (optional)
    var.cluster_policy_spark_version != null ? {
      "spark_version" = {
        "type"  = "fixed"
        "value" = var.cluster_policy_spark_version
      }
    } : {},
  ))
}

# =============================================================================
# Shared Interactive Cluster (optional)
# =============================================================================
# An always-available cluster for interactive notebook development.
# Auto-terminates after idle period to save costs.
# If a cluster policy is enabled, the cluster uses it.
# =============================================================================

resource "databricks_cluster" "shared" {
  count = var.enable_cluster ? 1 : 0

  cluster_name            = var.cluster_name
  spark_version           = var.cluster_spark_version
  node_type_id            = var.cluster_node_type
  num_workers             = var.cluster_num_workers
  autotermination_minutes = var.cluster_autotermination_minutes

  # Attach to policy if one exists
  policy_id = var.enable_cluster_policy ? databricks_cluster_policy.this[0].id : null

  spark_conf = merge(
    { "spark.databricks.delta.preview.enabled" = "true" },
    var.cluster_spark_conf,
  )

  custom_tags = var.tags
}

# =============================================================================
# Pipeline Job with Ephemeral Cluster (optional)
# =============================================================================
# Creates a Databricks Job that runs the pipeline notebook on a fresh
# short-lived cluster. The cluster starts when the job runs and terminates
# immediately after — no idle costs.
# =============================================================================

resource "databricks_job" "pipeline" {
  count = var.enable_pipeline_job ? 1 : 0

  name = var.pipeline_job_name

  task {
    task_key = "run_pipeline"

    notebook_task {
      notebook_path   = var.pipeline_notebook_path
      base_parameters = var.pipeline_notebook_params
    }

    new_cluster {
      spark_version = var.cluster_spark_version
      node_type_id  = var.pipeline_job_node_type
      num_workers   = var.pipeline_job_num_workers

      # Attach to policy if one exists
      policy_id = var.enable_cluster_policy ? databricks_cluster_policy.this[0].id : null

      custom_tags = var.tags
    }
  }

  # Schedule — only if cron expression is provided
  dynamic "schedule" {
    for_each = var.pipeline_schedule_cron != null ? [1] : []
    content {
      quartz_cron_expression = var.pipeline_schedule_cron
      timezone_id            = var.pipeline_schedule_timezone
    }
  }
}
