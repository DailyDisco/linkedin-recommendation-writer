#!/bin/bash
# =============================================================================
# LinkedIn Recommendation Writer - Health Check Script
# =============================================================================
# Usage: ./health-check.sh [--json]
#
# Checks the health of all deployments and infrastructure.
# =============================================================================

# Configuration
# Use appstack's caddy directory (volume-mounted into Caddy container)
CADDY_ACTIVE_DIR="${CADDY_ACTIVE_DIR:-/srv/vault/appstack/caddy/active-deployment}"

# Parse arguments
JSON_OUTPUT=false
for arg in "$@"; do
    case $arg in
        --json) JSON_OUTPUT=true ;;
    esac
done

# Colors (disabled for JSON output)
if [[ "$JSON_OUTPUT" == "false" ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

check_deployment() {
    local color=$1
    local container="linkedin-recommender-app-$color"
    local status="unknown"
    local response=""

    # Check if container exists
    if ! docker ps -a --filter "name=$container" --format "{{.Names}}" | grep -q "$container"; then
        status="not_found"
    # Check if container is running
    elif ! docker ps --filter "name=$container" --format "{{.Names}}" | grep -q "$container"; then
        status="stopped"
    else
        # Check health endpoint
        response=$(docker exec "$container" curl -sf http://localhost:8000/health 2>/dev/null || echo "")

        if [[ -z "$response" ]]; then
            status="unhealthy"
        else
            local health_status
            health_status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "")

            case "$health_status" in
                "healthy"|"ok") status="healthy" ;;
                "degraded") status="degraded" ;;
                *) status="unhealthy" ;;
            esac
        fi
    fi

    if [[ "$JSON_OUTPUT" == "true" ]]; then
        echo "{\"color\":\"$color\",\"status\":\"$status\",\"container\":\"$container\"}"
    else
        local status_color
        case "$status" in
            "healthy") status_color="${GREEN}HEALTHY${NC}" ;;
            "degraded") status_color="${YELLOW}DEGRADED${NC}" ;;
            "stopped") status_color="${YELLOW}STOPPED${NC}" ;;
            "not_found") status_color="${BLUE}NOT DEPLOYED${NC}" ;;
            *) status_color="${RED}UNHEALTHY${NC}" ;;
        esac

        echo -e "  $color: $status_color"
        if [[ -n "$response" && "$status" != "not_found" ]]; then
            echo "    Response: $response"
        fi
    fi
}

check_infrastructure() {
    local service=$1
    local container=$2
    local check_cmd=$3
    local status="unknown"

    if ! docker ps --filter "name=$container" --format "{{.Names}}" | grep -q "$container"; then
        status="stopped"
    else
        if docker exec "$container" sh -c "$check_cmd" > /dev/null 2>&1; then
            status="healthy"
        else
            status="unhealthy"
        fi
    fi

    if [[ "$JSON_OUTPUT" == "true" ]]; then
        echo "{\"service\":\"$service\",\"status\":\"$status\",\"container\":\"$container\"}"
    else
        local status_color
        case "$status" in
            "healthy") status_color="${GREEN}HEALTHY${NC}" ;;
            "stopped") status_color="${YELLOW}STOPPED${NC}" ;;
            *) status_color="${RED}UNHEALTHY${NC}" ;;
        esac
        echo -e "  $service: $status_color"
    fi
}

get_active_color() {
    if [[ -f "$CADDY_ACTIVE_DIR/linkedin-green" ]]; then
        echo "green"
    elif [[ -f "$CADDY_ACTIVE_DIR/linkedin-blue" ]]; then
        echo "blue"
    else
        echo "blue (default)"
    fi
}

main() {
    local active_color
    active_color=$(get_active_color)

    if [[ "$JSON_OUTPUT" == "true" ]]; then
        echo "{"
        echo "  \"active_deployment\": \"$active_color\","
        echo "  \"deployments\": ["
        echo -n "    "
        check_deployment "blue"
        echo ","
        echo -n "    "
        check_deployment "green"
        echo ""
        echo "  ],"
        echo "  \"infrastructure\": ["
        echo -n "    "
        check_infrastructure "postgres" "linkedin-recommender-postgres" "pg_isready -U postgres"
        echo ","
        echo -n "    "
        check_infrastructure "redis" "linkedin-recommender-redis" "redis-cli ping"
        echo ""
        echo "  ]"
        echo "}"
    else
        echo ""
        echo "=========================================="
        echo "LinkedIn Recommender Health Status"
        echo "=========================================="
        echo ""
        echo -e "Active Deployment: ${GREEN}$active_color${NC}"
        echo ""
        echo "Deployments:"
        check_deployment "blue"
        check_deployment "green"
        echo ""
        echo "Infrastructure:"
        check_infrastructure "PostgreSQL" "linkedin-recommender-postgres" "pg_isready -U postgres"
        check_infrastructure "Redis" "linkedin-recommender-redis" "redis-cli ping"
        echo ""
        echo "=========================================="
        echo ""
    fi
}

main "$@"
