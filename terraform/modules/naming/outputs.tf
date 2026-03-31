output "region_short" {
  description = "Short region code for resource naming (e.g., westeurope → weu)"
  value       = lookup(local.region_short_map, var.location, replace(var.location, "/[aeiou]/", ""))
}
