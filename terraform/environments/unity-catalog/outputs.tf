# =============================================================================
# Unity Catalog Outputs
# =============================================================================

# Note: metastore is auto-created & auto-assigned by Azure when the workspace
# is provisioned. Its ID can be retrieved at any time via:
#   curl -H "Authorization: Bearer $TOKEN" \
#     "https://<workspace-url>/api/2.1/unity-catalog/metastore_summary"

# --- Dev catalog ---
output "dev_catalog_name" {
  description = "Dev environment catalog name"
  value       = module.dev_catalog.catalog_name
}

output "dev_bronze_schema" {
  value = module.dev_catalog.bronze_schema
}

output "dev_silver_schema" {
  value = module.dev_catalog.silver_schema
}

output "dev_gold_schema" {
  value = module.dev_catalog.gold_schema
}

# --- Prod catalog ---
output "prod_catalog_name" {
  description = "Prod environment catalog name"
  value       = module.prod_catalog.catalog_name
}

output "prod_bronze_schema" {
  value = module.prod_catalog.bronze_schema
}

output "prod_silver_schema" {
  value = module.prod_catalog.silver_schema
}

output "prod_gold_schema" {
  value = module.prod_catalog.gold_schema
}
