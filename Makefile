.PHONY: install dev dev-frontend build validate deploy-dev deploy-staging deploy-prod requirements

# Load environment variables
include .env
export

# Installation des dépendances
install:
	uv sync
	cd frontend && npm install

# Développement local
dev:
	uv run uvicorn src.wind_turbine_analytics.api.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

# Build production
build:
	cd frontend && npm run build

# Validation bundle
validate:
	databricks bundle validate --target dev

# Déploiement
deploy-dev:
	databricks bundle deploy --target dev

deploy-staging:
	databricks bundle deploy -t staging

deploy-prod:
	databricks bundle deploy -t production

# Export requirements.txt
requirements:
	uv pip compile pyproject.toml -o requirements.txt
