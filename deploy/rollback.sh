#!/bin/bash
set -euo pipefail

# ============================================================
# ScanifyMe Rollback Script
# Emergency rollback for failed deployments
# ============================================================

DEPLOY_DIR="/opt/scanifyme"
SITE_NAME="scanifyme.app"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

show_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  status      - Show current deployment status"
    echo "  restart     - Restart all services"
    echo "  logs        - Show recent logs from all containers"
    echo "  diagnose    - Run diagnostic checks"
    echo "  help        - Show this help"
    echo ""
}

show_status() {
    log "========== DEPLOYMENT STATUS =========="
    
    cd "$DEPLOY_DIR"
    
    echo "=== Container Status ==="
    docker ps
    
    echo ""
    echo "=== Disk Usage ==="
    df -h /
    
    echo ""
    echo "=== Docker Resources ==="
    docker system df
    
    echo ""
    echo "=== Recent Logs (Backend) ==="
    docker logs scanifyme-backend-1 --tail 20 2>&1 | grep -E "ERROR|error|Error" || echo "No errors found"
    
    echo ""
    echo "=== Recent Logs (Frontend) ==="
    docker logs scanifyme-frontend-1 --tail 20 2>&1 | grep -E "404|500|error" || echo "No errors found"
}

restart_services() {
    log "========== RESTARTING SERVICES =========="
    
    cd "$DEPLOY_DIR"
    
    log "Stopping containers..."
    docker compose --env-file .env -f compose.prod.yaml down
    
    log "Starting containers..."
    docker compose --env-file .env -f compose.prod.yaml up -d
    
    log "Waiting for services to start..."
    sleep 15
    
    log_success "Services restarted"
    
    show_status
}

show_logs() {
    log "========== RECENT LOGS =========="
    
    echo "=== Backend Logs (last 50 lines) ==="
    docker logs scanifyme-backend-1 --tail 50 2>&1
    
    echo ""
    echo "=== Frontend Logs (last 50 lines) ==="
    docker logs scanifyme-frontend-1 --tail 50 2>&1
    
    echo ""
    echo "=== Database Logs (last 20 lines) ==="
    docker logs scanifyme-db-1 --tail 20 2>&1
}

run_diagnostics() {
    log "========== DIAGNOSTICS =========="
    
    cd "$DEPLOY_DIR"
    
    local issues=0
    
    # Check if all containers are running
    echo "=== Container Health ==="
    local expected_containers=10
    local running_containers=$(docker ps -q | wc -l)
    if [ "$running_containers" -lt "$expected_containers" ]; then
        log_error "Only $running_containers containers running (expected $expected_containers)"
        issues=$((issues + 1))
    else
        log_success "All containers running ($running_containers)"
    fi
    
    # Check for unhealthy containers
    local unhealthy=$(docker ps --filter "health=unhealthy" -q | wc -l)
    if [ "$unhealthy" -gt 0 ]; then
        log_error "$unhealthy unhealthy containers found"
        issues=$((issues + 1))
    else
        log_success "No unhealthy containers"
    fi
    
    # Check for restarting containers
    local restarting=$(docker ps --filter "status=restarting" -q | wc -l)
    if [ "$restarting" -gt 0 ]; then
        log_error "$restarting containers in restart loop"
        issues=$((issues + 1))
    else
        log_success "No restart loops"
    fi
    
    # Check disk space
    echo ""
    echo "=== Disk Space ==="
    local available_disk=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$available_disk" -lt 5 ]; then
        log_error "Critical disk space: ${available_disk}GB available"
        issues=$((issues + 1))
    elif [ "$available_disk" -lt 10 ]; then
        log_warning "Low disk space: ${available_disk}GB available"
    else
        log_success "Disk space OK: ${available_disk}GB available"
    fi
    
    # Check API
    echo ""
    echo "=== API Health ==="
    if curl -s http://localhost:8080/api/method/ping | grep -q "pong"; then
        log_success "API is responding"
    else
        log_error "API is not responding"
        issues=$((issues + 1))
    fi
    
    # Check frontend
    echo ""
    echo "=== Frontend Health ==="
    if curl -s http://localhost:8080/frontend | grep -q "doctype html"; then
        log_success "Frontend is loading"
    else
        log_error "Frontend is not loading"
        issues=$((issues + 1))
    fi
    
    echo ""
    if [ $issues -eq 0 ]; then
        log_success "All diagnostics passed"
    else
        log_error "$issues issues found"
    fi
    
    return $issues
}

main() {
    local command="${1:-status}"
    
    case "$command" in
        status)
            show_status
            ;;
        restart)
            restart_services
            ;;
        logs)
            show_logs
            ;;
        diagnose)
            run_diagnostics
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
