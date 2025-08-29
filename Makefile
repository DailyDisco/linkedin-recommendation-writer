# LinkedIn Recommendation Writer - Docker Development Commands
.PHONY: help build up down logs clean test prod prod-up prod-down

# Default target
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ============================
# Development Commands
# ============================

build: ## Build all services for development
	docker compose build

build-no-cache: ## Build all services without cache
	docker compose build --no-cache

up: ## Start all services in development mode
	docker compose up -d

up-logs: ## Start all services and show logs
	docker compose up

down: ## Stop all services
	docker compose down -v

logs: ## Show logs from all services
	docker compose logs -f app

restart: ## Restart all services
	docker compose restart

# ============================
# Testing & Linting
# ============================

test-frontend: ## Run frontend tests
	docker compose exec app sh -c "cd /app/frontend && npm run test"

lint-frontend: ## Run frontend linting
	docker compose exec app sh -c "cd /app/frontend && npm run lint"

format-frontend: ## Format frontend code
	docker compose exec app sh -c "cd /app/frontend && npm run prettier:fix"

test-backend: ## Run backend tests
	docker compose exec app sh -c "cd /app/backend && pytest"

lint-backend: ## Run backend linting
	docker compose exec app sh -c "cd /app/backend && black . --check && isort . --check-only && flake8 ."

format-backend: ## Format backend code
	docker compose exec app sh -c "cd /app/backend && black . && isort ."

# ============================
# Production Commands
# ============================

prod-build: ## Build all services for production
	docker compose -f docker-compose.prod.yml build

prod-up: ## Start all services in production mode
	docker compose -f docker-compose.prod.yml up -d

prod-down: ## Stop all production services
	docker compose -f docker-compose.prod.yml down -v

prod-logs: ## Show production logs
	docker compose -f docker-compose.prod.yml logs -f nginx app

# ============================
# Utility Commands
# ============================

clean: ## Remove all containers, volumes, and images associated with this project
	docker compose down -v --rmi all
	docker compose -f docker-compose.prod.yml down -v --rmi all

shell: ## Open a shell in the main app container
	docker compose exec app bash

db-connect: ## Connect to the development database
	docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
