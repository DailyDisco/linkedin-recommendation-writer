# ============================================
# LinkedIn Recommendation Writer - Development
# ============================================

# Use bash for shell commands (required for nvm source)
SHELL := /bin/bash

.PHONY: help dev dev-attached dev-down dev-destroy dev-fresh build rebuild restart down \
        logs logs-app logs-db logs-redis tail \
        test test-frontend test-backend lint lint-frontend lint-backend format format-frontend format-backend \
        db-seed db-seed-clean db-seed-minimal db-migrate db-migrate-down db-reset db-connect \
        prod prod-build prod-down prod-logs \
        deploy deploy-skip-pull rollback rollback-stop health health-json health-dev \
        bg-logs-blue bg-logs-green bg-shell-blue bg-shell-green bg-infra bg-backup \
        clean shell status ps setup

# ============================================
# Configuration
# ============================================

ENV_FILE := .env

# Database (defaults match docker-compose.yml)
POSTGRES_USER     ?= postgres
POSTGRES_PASSWORD ?= postgres
POSTGRES_DB       ?= github_recommender
POSTGRES_PORT     ?= 5432

# Ports
APP_PORT   ?= 8000
REDIS_PORT ?= 6379

# NVM npm command (for local fallback when Docker unavailable)
# Sources nvm to make npm available in non-interactive shells
NPM_LOCAL = source "$$HOME/.nvm/nvm.sh" && npm

# Blue-Green Deployment
BG_DIR     := /srv/linkedin-recommender
BG_SCRIPTS := $(BG_DIR)/scripts

# ============================================
# Compose Commands (DRY)
# ============================================

DC      := docker compose
DC_PROD := docker compose -f docker-compose.prod.yml
DC_BG   := docker compose -f $(BG_DIR)/docker-compose.blue-green.yml --env-file $(BG_DIR)/.env.production

# ============================================
# Help
# ============================================

help: ## Show this help message
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ============================================
# Development
# ============================================

dev: ## Start all services in development mode
	@$(DC) up -d
	@echo "Services starting... Run 'make logs' to watch."

dev-attached: ## Start all services with logs attached (foreground)
	@$(DC) up

dev-down: ## Stop all services
	@$(DC) down

dev-destroy: ## Stop all services and remove volumes
	@$(DC) down -v

dev-fresh: ## Start dev with fresh database
	@$(DC) down -v
	@$(DC) up -d
	@echo "Fresh database created. Run 'make db-seed' to populate."

restart: ## Restart all services
	@$(DC) restart

down: ## Stop all running containers (dev + prod)
	@$(DC) down
	@$(DC_PROD) down 2>/dev/null || true

# ============================================
# Build
# ============================================

build: ## Build all services for development
	@$(DC) build

rebuild: ## Rebuild all services without cache
	@$(DC) build --no-cache

# ============================================
# Logs
# ============================================

logs: ## Show logs from all services (follow)
	@$(DC) logs -f

logs-app: ## Show logs from app service only
	@$(DC) logs -f app

logs-db: ## Show logs from postgres service
	@$(DC) logs -f postgres

logs-redis: ## Show logs from redis service
	@$(DC) logs -f redis

tail: ## Show last 100 lines of logs
	@$(DC) logs --tail=100

# ============================================
# Testing
# ============================================

test: test-backend test-frontend ## Run all tests

test-frontend: ## Run frontend tests
	@echo "Running frontend tests..."
	@$(DC) exec -T app sh -c "cd /app/frontend && npm run test" 2>/dev/null || \
		(cd frontend && $(NPM_LOCAL) run test)

test-backend: ## Run backend tests
	@echo "Running backend tests..."
	@$(DC) exec -T app sh -c "cd /app/backend && pytest" 2>/dev/null || \
		(cd backend && pytest)

# ============================================
# Linting
# ============================================

lint: lint-backend lint-frontend ## Run all linters

lint-frontend: ## Run frontend linting
	@echo "Running frontend linting..."
	@$(DC) exec -T app sh -c "cd /app/frontend && npm run lint" 2>/dev/null || \
		(cd frontend && $(NPM_LOCAL) run lint)

lint-backend: ## Run backend linting
	@echo "Running backend linting..."
	@$(DC) exec -T app sh -c "cd /app/backend && black . --check && isort . --check-only && flake8 ." 2>/dev/null || \
		(cd backend && black . --check && isort . --check-only && flake8 .)

# ============================================
# Formatting
# ============================================

format: format-backend format-frontend ## Format all code

format-frontend: ## Format frontend code
	@$(DC) exec -T app sh -c "cd /app/frontend && npm run prettier:fix" 2>/dev/null || \
		(cd frontend && $(NPM_LOCAL) run prettier:fix)

format-backend: ## Format backend code
	@$(DC) exec -T app sh -c "cd /app/backend && black . && isort ." 2>/dev/null || \
		(cd backend && black . && isort .)

# ============================================
# Database
# ============================================

db-seed: ## Seed database with test data
	@$(DC) exec app sh -c "cd /app/backend && python -m app.scripts.seed"

db-seed-clean: ## Clean and reseed database
	@$(DC) exec app sh -c "cd /app/backend && python -m app.scripts.seed --clean"

db-seed-minimal: ## Seed database with minimal data
	@$(DC) exec app sh -c "cd /app/backend && python -m app.scripts.seed --minimal"

db-migrate: ## Run database migrations
	@$(DC) exec app sh -c "cd /app/backend && alembic upgrade head"

db-migrate-down: ## Rollback last migration
	@$(DC) exec app sh -c "cd /app/backend && alembic downgrade -1"

db-reset: ## Reset database (WARNING: deletes all data)
	@$(DC) down -v
	@$(DC) up -d postgres redis
	@echo "Database reset. Run 'make dev' to start all services."

db-connect: ## Connect to the development database
	@$(DC) exec postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

# ============================================
# Shell Access
# ============================================

shell: ## Open a shell in the main app container
	@$(DC) exec app bash

shell-db: db-connect ## Alias for db-connect

# ============================================
# Status & Health
# ============================================

status: ps ## Alias for ps

ps: ## Show status of all services
	@$(DC) ps

health-dev: ## Check health of development services
	@printf "App:      " && curl -sf http://localhost:$(APP_PORT)/health >/dev/null 2>&1 && echo "✓ healthy" || echo "✗ not healthy"
	@printf "Redis:    " && $(DC) exec -T redis redis-cli ping >/dev/null 2>&1 && echo "✓ ready" || echo "✗ not ready"
	@printf "Postgres: " && $(DC) exec -T postgres pg_isready -U $(POSTGRES_USER) -d $(POSTGRES_DB) >/dev/null 2>&1 && echo "✓ ready" || echo "✗ not ready"

# ============================================
# Production
# ============================================

prod: ## Start all services in production mode
	@$(DC_PROD) up -d

prod-build: ## Build all services for production
	@$(DC_PROD) build

prod-down: ## Stop all production services
	@$(DC_PROD) down -v

prod-logs: ## Show production logs
	@$(DC_PROD) logs -f nginx app

# ============================================
# Blue-Green Deployment
# ============================================
# These commands are for production blue-green deployments
# Files are in deployment/blue-green/

deploy: ## Deploy to inactive color (blue-green deployment)
	@bash $(BG_SCRIPTS)/deploy.sh

deploy-skip-pull: ## Deploy without pulling latest code
	@bash $(BG_SCRIPTS)/deploy.sh --skip-pull

rollback: ## Rollback to previous deployment
	@bash $(BG_SCRIPTS)/rollback.sh

rollback-stop: ## Rollback and stop failed deployment
	@bash $(BG_SCRIPTS)/rollback.sh --stop-failed

health: ## Check health of all deployments
	@bash $(BG_SCRIPTS)/health-check.sh

health-json: ## Check health (JSON output)
	@bash $(BG_SCRIPTS)/health-check.sh --json

bg-logs-blue: ## Show blue deployment logs
	@docker logs -f linkedin-recommender-app-blue

bg-logs-green: ## Show green deployment logs
	@docker logs -f linkedin-recommender-app-green

bg-shell-blue: ## Open shell in blue deployment
	@docker exec -it linkedin-recommender-app-blue bash

bg-shell-green: ## Open shell in green deployment
	@docker exec -it linkedin-recommender-app-green bash

bg-infra: ## Start shared infrastructure (postgres, redis)
	@$(DC_BG) up -d postgres redis

bg-backup: ## Backup production database
	@mkdir -p $(BG_DIR)/backups
	@docker exec linkedin-recommender-postgres pg_dump -U postgres github_recommender | gzip > $(BG_DIR)/backups/manual_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "Backup created at $(BG_DIR)/backups/"

# ============================================
# Cleanup
# ============================================

clean: ## Remove all containers, volumes, and images
	@$(DC) down -v --remove-orphans
	@$(DC_PROD) down -v --remove-orphans 2>/dev/null || true
	@docker system prune -f

# ============================================
# Setup
# ============================================

setup: ## Initial setup - copy env file
	@if [ -f .env ]; then \
		echo "Warning: .env already exists. Remove it first to reset."; \
	else \
		cp .env.example .env && \
		echo "Created .env from .env.example" && \
		echo "Customize as needed, then run 'make dev'."; \
	fi
