#!/bin/bash
# =============================================================================
# LinkedIn Recommendation Writer - Blue-Green Deployment Script
# =============================================================================
# Usage: ./deploy.sh [--skip-pull] [--skip-backup]
#
# This script:
# 1. Determines the currently active deployment (blue or green)
# 2. Deploys to the inactive color
# 3. Runs health checks
# 4. Switches traffic via Caddy marker files
# 5. Keeps old deployment running for quick rollback
# =============================================================================
set -euo pipefail

# Configuration - adjust these paths for your setup
DEPLOY_DIR="${DEPLOY_DIR:-/srv/linkedin-recommender}"
REPO_DIR="${REPO_DIR:-/home/day/Programming_Projects_Modern/github_repo_linkedin_recommendation_writer_app}"
# Use appstack's caddy directory (volume-mounted into Caddy container)
CADDY_ACTIVE_DIR="${CADDY_ACTIVE_DIR:-/srv/vault/appstack/caddy/active-deployment}"
COMPOSE_FILE="$DEPLOY_DIR/docker-compose.blue-green.yml"
ENV_FILE="$DEPLOY_DIR/.env.production"

# Health check settings
HEALTH_TIMEOUT=120
HEALTH_INTERVAL=5

# Parse arguments
SKIP_PULL=false
SKIP_BACKUP=false
for arg in "$@"; do
    case $arg in
        --skip-pull) SKIP_PULL=true ;;
        --skip-backup) SKIP_BACKUP=true ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

get_active_color() {
    if [[ -f "$CADDY_ACTIVE_DIR/linkedin-green" ]]; then
        echo "green"
    else
        echo "blue"  # Default to blue
    fi
}

get_inactive_color() {
    local active
    active=$(get_active_color)
    if [[ "$active" == "blue" ]]; then
        echo "green"
    else
        echo "blue"
    fi
}

ensure_directories() {
    log_info "Ensuring directories exist..."
    mkdir -p "$DEPLOY_DIR/backups"
    mkdir -p "$DEPLOY_DIR/logs"
    sudo mkdir -p "$CADDY_ACTIVE_DIR"
}

health_check() {
    local color=$1
    local container="linkedin-recommender-app-$color"
    local elapsed=0

    log_info "Waiting for $color deployment to be healthy..."

    while [[ $elapsed -lt $HEALTH_TIMEOUT ]]; do
        # Check if container is running
        if ! docker ps --filter "name=$container" --format "{{.Names}}" | grep -q "$container"; then
            log_warning "Container $container not running yet..."
            sleep $HEALTH_INTERVAL
            elapsed=$((elapsed + HEALTH_INTERVAL))
            continue
        fi

        # Check health endpoint
        local health_response
        health_response=$(docker exec "$container" curl -sf http://localhost:8000/health 2>/dev/null || echo "")

        if [[ -n "$health_response" ]]; then
            local status
            status=$(echo "$health_response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "")

            if [[ "$status" == "healthy" || "$status" == "ok" ]]; then
                log_success "$color deployment is healthy!"
                return 0
            elif [[ "$status" == "degraded" ]]; then
                log_warning "$color deployment is degraded but functional"
                return 0
            fi
        fi

        sleep $HEALTH_INTERVAL
        elapsed=$((elapsed + HEALTH_INTERVAL))
        log_info "Health check attempt... ($elapsed/$HEALTH_TIMEOUT seconds)"
    done

    log_error "Health check timed out for $color deployment"
    return 1
}

switch_traffic() {
    local target_color=$1

    log_info "Switching traffic to $target_color deployment..."

    # Remove all existing markers
    rm -f "$CADDY_ACTIVE_DIR/linkedin-blue"
    rm -f "$CADDY_ACTIVE_DIR/linkedin-green"

    # Create marker for target color
    touch "$CADDY_ACTIVE_DIR/linkedin-$target_color"

    # Reload Caddy (running in appstack Docker)
    if docker ps --format '{{.Names}}' | grep -q '^caddy$'; then
        docker exec caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile 2>/dev/null || \
            log_warning "Caddy reload failed - Caddy will pick up changes on next request"
    else
        log_warning "Caddy container not found - ensure it's running"
    fi

    log_success "Traffic switched to $target_color"
}

run_migrations() {
    local color=$1
    local container="linkedin-recommender-app-$color"

    log_info "Running database migrations..."

    docker exec "$container" sh -c "cd /app/backend && alembic upgrade head" || {
        log_error "Migration failed!"
        return 1
    }

    log_success "Migrations completed successfully"
}

backup_database() {
    if [[ "$SKIP_BACKUP" == "true" ]]; then
        log_warning "Skipping database backup (--skip-backup)"
        return 0
    fi

    log_info "Creating database backup..."

    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$DEPLOY_DIR/backups/pre_deploy_$timestamp.sql"

    docker exec linkedin-recommender-postgres pg_dump -U postgres github_recommender > "$backup_file" 2>/dev/null || {
        log_warning "Database backup failed, continuing anyway..."
        return 0
    }

    gzip "$backup_file" 2>/dev/null || true
    log_success "Database backup created: ${backup_file}.gz"
}

pull_latest_code() {
    if [[ "$SKIP_PULL" == "true" ]]; then
        log_warning "Skipping git pull (--skip-pull)"
        return 0
    fi

    log_info "Pulling latest code..."
    cd "$REPO_DIR"
    git pull origin master || {
        log_error "Failed to pull latest code"
        exit 1
    }
}

# =============================================================================
# MAIN DEPLOYMENT FLOW
# =============================================================================

main() {
    echo ""
    log_info "=============================="
    log_info "Blue-Green Deployment Starting"
    log_info "=============================="
    echo ""

    # Ensure directories exist
    ensure_directories

    # Determine colors
    local active_color
    local deploy_color
    active_color=$(get_active_color)
    deploy_color=$(get_inactive_color)

    log_info "Current active: $active_color"
    log_info "Deploying to:   $deploy_color"
    echo ""

    # Step 1: Pull latest code
    log_info "Step 1/7: Pulling latest code..."
    pull_latest_code

    # Step 2: Backup database
    log_info "Step 2/7: Backing up database..."
    backup_database

    # Step 3: Build new image
    log_info "Step 3/7: Building $deploy_color image..."
    cd "$DEPLOY_DIR"

    if [[ "$deploy_color" == "green" ]]; then
        docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" \
            --profile green build "app-$deploy_color" || {
            log_error "Build failed!"
            exit 1
        }
    else
        docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" \
            build "app-$deploy_color" || {
            log_error "Build failed!"
            exit 1
        }
    fi

    # Step 4: Start inactive deployment
    log_info "Step 4/7: Starting $deploy_color deployment..."

    if [[ "$deploy_color" == "green" ]]; then
        docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" \
            --profile green up -d "app-$deploy_color"
    else
        docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" \
            up -d "app-$deploy_color"
    fi

    # Step 5: Health check
    log_info "Step 5/7: Running health checks..."
    if ! health_check "$deploy_color"; then
        log_error "Deployment failed health check!"
        log_info "Rolling back - stopping $deploy_color..."
        docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop "app-$deploy_color"
        exit 1
    fi

    # Step 6: Run migrations
    log_info "Step 6/7: Running database migrations..."
    if ! run_migrations "$deploy_color"; then
        log_error "Migration failed!"
        log_info "Rolling back - stopping $deploy_color..."
        docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop "app-$deploy_color"
        exit 1
    fi

    # Brief pause after migrations
    sleep 5

    # Verify health after migrations
    if ! health_check "$deploy_color"; then
        log_error "Post-migration health check failed!"
        log_info "Rolling back..."
        docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop "app-$deploy_color"
        exit 1
    fi

    # Step 7: Switch traffic
    log_info "Step 7/7: Switching traffic..."
    switch_traffic "$deploy_color"

    echo ""
    log_success "=============================="
    log_success "Deployment Complete!"
    log_success "=============================="
    log_success "Active:  $deploy_color"
    log_success "Standby: $active_color (kept for rollback)"
    log_success ""
    log_success "Run './scripts/rollback.sh' if issues occur"
    log_success "=============================="
    echo ""
}

main "$@"
