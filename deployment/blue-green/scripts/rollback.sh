#!/bin/bash
# =============================================================================
# LinkedIn Recommendation Writer - Rollback Script
# =============================================================================
# Usage: ./rollback.sh [--stop-failed]
#
# Quickly switches traffic back to the previous deployment.
# =============================================================================
set -euo pipefail

# Configuration
DEPLOY_DIR="${DEPLOY_DIR:-/srv/linkedin-recommender}"
# Use appstack's caddy directory (volume-mounted into Caddy container)
CADDY_ACTIVE_DIR="${CADDY_ACTIVE_DIR:-/srv/vault/appstack/caddy/active-deployment}"
COMPOSE_FILE="$DEPLOY_DIR/docker-compose.blue-green.yml"
ENV_FILE="$DEPLOY_DIR/.env.production"

# Parse arguments
STOP_FAILED=false
for arg in "$@"; do
    case $arg in
        --stop-failed) STOP_FAILED=true ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()    { echo -e "${YELLOW}[ROLLBACK]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

get_active_color() {
    if [[ -f "$CADDY_ACTIVE_DIR/linkedin-green" ]]; then
        echo "green"
    else
        echo "blue"
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

quick_health_check() {
    local color=$1
    local container="linkedin-recommender-app-$color"

    # Check if container exists and is running
    if ! docker ps --filter "name=$container" --format "{{.Names}}" | grep -q "$container"; then
        return 1
    fi

    # Quick health check
    local response
    response=$(docker exec "$container" curl -sf http://localhost:8000/health 2>/dev/null || echo "")

    if [[ -n "$response" ]]; then
        return 0
    fi

    return 1
}

main() {
    echo ""
    log_info "=============================="
    log_info "Starting Rollback"
    log_info "=============================="
    echo ""

    local current_active
    local rollback_to
    current_active=$(get_active_color)
    rollback_to=$(get_inactive_color)

    log_info "Current active: $current_active"
    log_info "Rolling back to: $rollback_to"
    echo ""

    # Verify rollback target is running and healthy
    log_info "Verifying rollback target is healthy..."
    if ! quick_health_check "$rollback_to"; then
        log_error "Rollback target ($rollback_to) is not healthy!"
        log_error "Cannot rollback - the standby deployment is not available."
        exit 1
    fi

    log_success "Rollback target ($rollback_to) is healthy"

    # Switch traffic
    log_info "Switching traffic to $rollback_to..."
    rm -f "$CADDY_ACTIVE_DIR/linkedin-blue"
    rm -f "$CADDY_ACTIVE_DIR/linkedin-green"
    touch "$CADDY_ACTIVE_DIR/linkedin-$rollback_to"

    # Reload Caddy (running in appstack Docker)
    if docker ps --format '{{.Names}}' | grep -q '^caddy$'; then
        docker exec caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile 2>/dev/null || true
    fi

    log_success "Traffic switched to $rollback_to"

    # Optionally stop the failed deployment
    if [[ "$STOP_FAILED" == "true" ]]; then
        log_info "Stopping failed $current_active deployment..."
        docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop "app-$current_active"
        log_success "Stopped $current_active deployment"
    fi

    echo ""
    log_success "=============================="
    log_success "Rollback Complete!"
    log_success "=============================="
    log_success "Active: $rollback_to"
    if [[ "$STOP_FAILED" != "true" ]]; then
        log_info "Note: $current_active is still running"
        log_info "Stop it with: docker compose -f $COMPOSE_FILE stop app-$current_active"
    fi
    log_success "=============================="
    echo ""
}

main "$@"
