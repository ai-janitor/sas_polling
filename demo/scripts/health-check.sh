#!/bin/bash
# =============================================================================
# DATAFIT SERVICE HEALTH CHECK SCRIPT
# =============================================================================
# Purpose: Comprehensive health checking for DataFit services
# Usage: ./health-check.sh [--verbose] [--json]
# 
# Exit Codes:
# 0 - All services healthy
# 1 - One or more services unhealthy
# 2 - Configuration error
# =============================================================================

set -euo pipefail

# Load configuration
if [ -f "../config.dev.env" ]; then
    source "../config.dev.env"
else
    echo "Error: config.dev.env not found" >&2
    exit 2
fi

# Default options
VERBOSE=false
JSON_OUTPUT=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --json|-j)
            JSON_OUTPUT=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--verbose] [--json]"
            echo "  --verbose, -v    Show detailed output"
            echo "  --json, -j       Output in JSON format"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

# Service URLs
SUBMISSION_URL="http://localhost:${SUBMISSION_PORT}"
POLLING_URL="http://localhost:${POLLING_PORT}"

# Colors for output (disabled for JSON)
if [ "$JSON_OUTPUT" = false ]; then
    GREEN='\033[0;32m'
    RED='\033[0;31m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    GREEN=''
    RED=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# Health check function
check_service() {
    local service_name="$1"
    local url="$2"
    local timeout=5
    
    if [ "$VERBOSE" = true ] && [ "$JSON_OUTPUT" = false ]; then
        echo -e "${BLUE}Checking $service_name at $url...${NC}"
    fi
    
    # Check if service responds
    if ! response=$(curl -s -f --max-time $timeout "$url/health" 2>/dev/null); then
        return 1
    fi
    
    # Parse response
    local service=$(echo "$response" | jq -r '.service // "unknown"' 2>/dev/null || echo "unknown")
    local status=$(echo "$response" | jq -r '.status // "unknown"' 2>/dev/null || echo "unknown")
    local timestamp=$(echo "$response" | jq -r '.timestamp // "unknown"' 2>/dev/null || echo "unknown")
    
    # Store results in global variables
    case $service_name in
        "Job Submission")
            SUBMISSION_STATUS="$status"
            SUBMISSION_SERVICE="$service"
            SUBMISSION_TIMESTAMP="$timestamp"
            SUBMISSION_RESPONSE="$response"
            ;;
        "Job Polling")
            POLLING_STATUS="$status"
            POLLING_SERVICE="$service"
            POLLING_TIMESTAMP="$timestamp"
            POLLING_RESPONSE="$response"
            ;;
    esac
    
    if [ "$status" = "healthy" ]; then
        if [ "$VERBOSE" = true ] && [ "$JSON_OUTPUT" = false ]; then
            echo -e "  ${GREEN}✓ $service_name is healthy${NC}"
        fi
        return 0
    else
        if [ "$VERBOSE" = true ] && [ "$JSON_OUTPUT" = false ]; then
            echo -e "  ${RED}✗ $service_name is $status${NC}"
        fi
        return 1
    fi
}

# Initialize status variables
SUBMISSION_STATUS="unreachable"
SUBMISSION_SERVICE="unknown"
SUBMISSION_TIMESTAMP="unknown"
SUBMISSION_RESPONSE=""

POLLING_STATUS="unreachable"
POLLING_SERVICE="unknown"
POLLING_TIMESTAMP="unknown"
POLLING_RESPONSE=""

# Check services
submission_healthy=false
polling_healthy=false

if check_service "Job Submission" "$SUBMISSION_URL"; then
    submission_healthy=true
fi

if check_service "Job Polling" "$POLLING_URL"; then
    polling_healthy=true
fi

# Generate output
if [ "$JSON_OUTPUT" = true ]; then
    # JSON output
    cat <<EOF
{
    "timestamp": "$(date -Iseconds)",
    "overall_status": "$( [ "$submission_healthy" = true ] && [ "$polling_healthy" = true ] && echo "healthy" || echo "unhealthy")",
    "services": {
        "job_submission": {
            "url": "$SUBMISSION_URL",
            "status": "$SUBMISSION_STATUS",
            "service": "$SUBMISSION_SERVICE",
            "timestamp": "$SUBMISSION_TIMESTAMP",
            "healthy": $submission_healthy
        },
        "job_polling": {
            "url": "$POLLING_URL", 
            "status": "$POLLING_STATUS",
            "service": "$POLLING_SERVICE",
            "timestamp": "$POLLING_TIMESTAMP",
            "healthy": $polling_healthy
        }
    }
}
EOF
else
    # Human-readable output
    echo -e "${BLUE}DataFit Service Health Check${NC}"
    echo -e "${BLUE}============================${NC}"
    echo ""
    
    echo -e "${YELLOW}Job Submission Service:${NC}"
    echo "  URL: $SUBMISSION_URL"
    echo -e "  Status: $( [ "$submission_healthy" = true ] && echo -e "${GREEN}✓ Healthy${NC}" || echo -e "${RED}✗ $SUBMISSION_STATUS${NC}")"
    echo "  Service: $SUBMISSION_SERVICE"
    echo "  Last Check: $SUBMISSION_TIMESTAMP"
    echo ""
    
    echo -e "${YELLOW}Job Polling Service:${NC}"
    echo "  URL: $POLLING_URL"
    echo -e "  Status: $( [ "$polling_healthy" = true ] && echo -e "${GREEN}✓ Healthy${NC}" || echo -e "${RED}✗ $POLLING_STATUS${NC}")"
    echo "  Service: $POLLING_SERVICE"
    echo "  Last Check: $POLLING_TIMESTAMP"
    echo ""
    
    if [ "$submission_healthy" = true ] && [ "$polling_healthy" = true ]; then
        echo -e "${GREEN}Overall Status: All services healthy${NC}"
    else
        echo -e "${RED}Overall Status: One or more services unhealthy${NC}"
    fi
fi

# Exit with appropriate code
if [ "$submission_healthy" = true ] && [ "$polling_healthy" = true ]; then
    exit 0
else
    exit 1
fi