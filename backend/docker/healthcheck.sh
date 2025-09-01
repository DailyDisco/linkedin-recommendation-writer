#!/bin/bash
# Security-focused health check script

set -euo pipefail

# Configuration
HEALTH_URL="http://localhost:8000/health"
TIMEOUT=10
RETRIES=3

# Function to check HTTP response
check_http_response() {
    local url="$1"
    local timeout="$2"
    
    # Use curl with security options
    if command -v curl >/dev/null 2>&1; then
        response=$(curl -s -w "HTTPSTATUS:%{http_code};TIME:%{time_total}" \
                    --max-time "$timeout" \
                    --connect-timeout 5 \
                    --fail \
                    --silent \
                    --show-error \
                    "$url" 2>/dev/null || echo "CURL_FAILED")
        
        if [[ "$response" == "CURL_FAILED" ]]; then
            echo "Health check failed: Unable to connect to $url"
            return 1
        fi
        
        # Extract HTTP status code
        http_code=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://' | sed -e 's/;TIME.*//')
        
        # Extract response time
        response_time=$(echo "$response" | tr -d '\n' | sed -e 's/.*TIME://')
        
        # Check if HTTP status is successful (2xx or 3xx)
        if [[ $http_code -ge 200 && $http_code -lt 400 ]]; then
            echo "Health check passed: HTTP $http_code (${response_time}s)"
            return 0
        else
            echo "Health check failed: HTTP $http_code (${response_time}s)"
            return 1
        fi
    else
        echo "Health check failed: curl not available"
        return 1
    fi
}

# Function to check system resources
check_system_resources() {
    # Check memory usage (should be less than 90%)
    if command -v free >/dev/null 2>&1; then
        memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2 }')
        if [[ $memory_usage -gt 90 ]]; then
            echo "Health check failed: High memory usage ($memory_usage%)"
            return 1
        fi
    fi
    
    # Check disk usage (should be less than 90%)
    if command -v df >/dev/null 2>&1; then
        disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
        if [[ $disk_usage -gt 90 ]]; then
            echo "Health check failed: High disk usage ($disk_usage%)"
            return 1
        fi
    fi
    
    return 0
}

# Main health check logic
main() {
    local attempt=1
    local max_attempts="$RETRIES"
    
    echo "Starting health check at $(date)"
    
    while [[ $attempt -le $max_attempts ]]; do
        echo "Attempt $attempt/$max_attempts..."
        
        # Check HTTP endpoint
        if check_http_response "$HEALTH_URL" "$TIMEOUT"; then
            # Check system resources
            if check_system_resources; then
                echo "✅ All health checks passed"
                exit 0
            fi
        fi
        
        if [[ $attempt -lt $max_attempts ]]; then
            echo "Retrying in 5 seconds..."
            sleep 5
        fi
        
        ((attempt++))
    done
    
    echo "❌ Health check failed after $max_attempts attempts"
    exit 1
}

# Run main function
main "$@"
