# LinkedIn Recommendation Writer - Docker Development Commands
.PHONY: help build up down logs clean test test-frontend test-backend prod prod-up prod-down

# Default target
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Development Commands:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -v '^\s*#'
	@echo ''
	@echo 'Available targets:'

# ============================
# Development Commands
# ============================

build: ## Build all services for development
	docker-compose build

build-no-cache: ## Build all services without cache
	docker-compose build --no-cache

up: ## Start all services in development mode
	docker-compose up -d

up-logs: ## Start all services and show logs
	docker-compose up

down: ## Stop all services
	docker-compose down

logs: ## Show logs from all services
	docker-compose logs -f

logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

logs-backend: ## Show backend logs
	docker-compose logs -f backend

restart: ## Restart all services
	docker-compose restart

restart-frontend: ## Restart frontend service
	docker-compose restart frontend

restart-backend: ## Restart backend service
	docker-compose restart backend

# ============================
# Testing Commands
# ============================

test: ## Run frontend tests
	@echo "Running frontend tests..."
	docker-compose exec frontend npm run test

test-frontend: ## Run frontend tests only
	docker-compose exec frontend npm run test

test-frontend-interactive: ## Run frontend tests interactively
	docker-compose exec frontend npm run test:ui

test-coverage: ## Run frontend tests with coverage
	docker-compose exec frontend npm run test:coverage

# ============================
# Production Commands
# ============================

prod-build: ## Build all services for production
	docker-compose -f docker-compose.prod.yml build

prod-up: ## Start all services in production mode
	docker-compose -f docker-compose.prod.yml up -d

prod-up-logs: ## Start production services and show logs
	docker-compose -f docker-compose.prod.yml up

prod-down: ## Stop production services
	docker-compose -f docker-compose.prod.yml down

prod-logs: ## Show production logs
	docker-compose -f docker-compose.prod.yml logs -f



# ============================
# Utility Commands
# ============================

clean: ## Remove all containers, volumes, and images
	docker-compose down -v --rmi all
	docker-compose -f docker-compose.prod.yml down -v --rmi all

clean-volumes: ## Remove all volumes
	docker volume rm $$(docker volume ls -q | grep linkedin-recommender) 2>/dev/null || true

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend sh

shell-backend: ## Open shell in backend container
	docker-compose exec backend bash

ps: ## Show running containers
	docker-compose ps

status: ## Show status of all services
	@echo "=== Development Services ==="
	docker-compose ps
	@echo ""
	@echo "=== Production Services ==="
	docker-compose -f docker-compose.prod.yml ps

# ============================
# Setup Commands
# ============================

setup: ## Initial setup - build and start services
	@echo "Setting up LinkedIn Recommendation Writer..."
	make build
	make up
	@echo "Services are starting up..."
	@echo "Frontend will be available at: http://localhost:5173"
	@echo "Backend will be available at: http://localhost:8000"
	@echo "Run 'make logs' to see the startup logs"

setup-prod: ## Production setup
	@echo "Setting up production environment..."
	docker-compose -f docker-compose.prod.yml build
	docker-compose -f docker-compose.prod.yml up -d
	@echo "Production services are starting up..."
	@echo "Application will be available at: http://localhost"
	@echo "Run 'make prod-logs' to see the startup logs"

# ============================
# Development Workflow Commands
# ============================

dev-frontend: ## Start frontend in development mode with logs
	docker-compose up frontend

dev-backend: ## Start backend in development mode with logs
	docker-compose up backend

dev-full: ## Start all services with logs (development)
	docker-compose up

# ============================
# Database Commands
# ============================

db-connect: ## Connect to development database
	docker-compose exec postgres psql -U postgres -d github_recommender

db-migrate: ## Run database migrations (development)
	docker-compose exec backend alembic upgrade head

# ============================
# Linting and Formatting
# ============================

lint-frontend: ## Run frontend linting
	docker-compose exec frontend npm run lint

lint-backend: ## Run backend linting
	docker-compose exec backend black . --check
	docker-compose exec backend isort . --check-only
	docker-compose exec backend flake8 .

format-frontend: ## Format frontend code
	docker-compose exec frontend npm run prettier:fix

format-backend: ## Format backend code
	docker-compose exec backend black .
	docker-compose exec backend isort .

# ============================
# Information Commands
# ============================

info: ## Show useful information
	@echo "=== LinkedIn Recommendation Writer ==="
	@echo ""
	@echo "Development URLs:"
	@echo "  Frontend: http://localhost:5173"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Database: localhost:5432"
	@echo "  Redis:    localhost:6379"
	@echo ""
	@echo "Production URLs:"
	@echo "  Application: http://localhost"
	@echo ""
	@echo "Useful commands:"
	@echo "  make logs              - Show all logs"
	@echo "  make test              - Run frontend tests"
	@echo "  make shell-frontend    - Open frontend shell"
	@echo "  make shell-backend     - Open backend shell"
	@echo "  make clean             - Remove all containers and volumes"
