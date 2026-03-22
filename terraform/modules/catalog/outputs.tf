output "catalog_name" {
  description = "Name of the environment catalog (same as environment name)"
  value       = databricks_catalog.this.name
}

output "bronze_schema" {
  description = "Full name of the bronze schema: {catalog}.bronze"
  value       = "${databricks_catalog.this.name}.${databricks_schema.bronze.name}"
}

output "silver_schema" {
  description = "Full name of the silver schema: {catalog}.silver"
  value       = "${databricks_catalog.this.name}.${databricks_schema.silver.name}"
}

output "gold_schema" {
  description = "Full name of the gold schema: {catalog}.gold"
  value       = "${databricks_catalog.this.name}.${databricks_schema.gold.name}"
}
