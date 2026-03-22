# =============================================================================
# Makefile — Convenience commands for the Azure Databricks Platform Demo
# =============================================================================
# NOTE: mise.toml is the recommended task runner for this project.
#       This Makefile is kept for users who prefer make or don't have mise.
#
# With mise:
#   mise run setup         One-time project setup
#   mise run validate      Run all CI checks
#   mise run deploy        Deploy infrastructure
#   mise tasks             List all tasks
#
# With make:
#   make help              Show all available commands
#   make deploy-dev        Deploy dev infrastructure
#   make generate-data     Generate sample sensor data
#   make destroy-dev       Tear down dev infrastructure
# =============================================================================

.PHONY: help deploy-dev deploy-prod destroy-dev destroy-prod generate-data generate-local setup-python

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------------------

deploy-dev: ## Deploy dev environment infrastructure
	cd terraform/environments/dev && \
		terraform init && \
		terraform plan && \
		terraform apply

deploy-prod: ## Deploy prod environment infrastructure
	cd terraform/environments/prod && \
		terraform init && \
		terraform plan && \
		terraform apply

destroy-dev: ## Destroy dev environment (saves costs!)
	cd terraform/environments/dev && \
		terraform destroy

destroy-prod: ## Destroy prod environment
	cd terraform/environments/prod && \
		terraform destroy

plan-dev: ## Preview dev environment changes
	cd terraform/environments/dev && \
		terraform init && \
		terraform plan

plan-prod: ## Preview prod environment changes
	cd terraform/environments/prod && \
		terraform init && \
		terraform plan

# ---------------------------------------------------------------------------
# Data Generator
# ---------------------------------------------------------------------------

setup-python: ## Set up Python virtual environment and install dependencies
	cd data_generator && \
		python -m venv .venv && \
		. .venv/bin/activate && \
		pip install -r requirements.txt

generate-data: ## Generate 10 batches of sensor data and upload to ADLS
	cd data_generator && \
		. .venv/bin/activate && \
		python generate_sensor_data.py --batches 10

generate-local: ## Generate sample data locally (no Azure credentials needed)
	cd data_generator && \
		. .venv/bin/activate && \
		python generate_sensor_data.py --local-only --batches 5

generate-continuous: ## Generate data continuously (Ctrl+C to stop)
	cd data_generator && \
		. .venv/bin/activate && \
		python generate_sensor_data.py --continuous --interval 15

# ---------------------------------------------------------------------------
# Info
# ---------------------------------------------------------------------------

outputs-dev: ## Show dev environment Terraform outputs
	cd terraform/environments/dev && \
		terraform output

outputs-prod: ## Show prod environment Terraform outputs
	cd terraform/environments/prod && \
		terraform output
