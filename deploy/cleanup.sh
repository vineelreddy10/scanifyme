#!/bin/bash
set -euo pipefail

DEPLOY_DIR="/opt/scanifyme"
MIN_DISK_GB=5

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

show_disk_status() {
    echo ""
    echo "Current Disk Status:"
    df -h / | head -2
    echo ""
}

cleanup_docker_images() {
    log "Cleaning Docker images..."
    
    local before=$(docker system df --format '{{.Size}}' | head -1)
    
    docker image prune -f 2>/dev/null || true
    
    local after=$(docker system df --format '{{.Size}}' | head -1)
    
    log_success "Docker images cleaned"
}

cleanup_docker_containers() {
    log "Cleaning stopped containers..."
    
    docker container prune -f 2>/dev/null || true
    
    log_success "Stopped containers removed"
}

cleanup_docker_volumes() {
    log_warning "Skipping volume cleanup (would delete database data)"
    echo "  Use 'docker volume prune' manually if needed"
}

cleanup_docker_networks() {
    log "Cleaning unused networks..."
    
    docker network prune -f 2>/dev/null || true
    
    log_success "Unused networks removed"
}

cleanup_docker_build_cache() {
    log "Cleaning Docker build cache..."
    
    docker builder prune -f 2>/dev/null || true
    
    log_success "Build cache cleaned"
}

cleanup_deploy_logs() {
    log "Cleaning old deployment logs..."
    
    local deleted=$(find /tmp -name "scanifyme-deploy-*.log" -type f -mtime +7 -delete -print | wc -l)
    
    log_success "Removed $deleted old deployment logs"
}

cleanup_old_backups() {
    log "Cleaning old backups..."
    
    if [ -d "${DEPLOY_DIR}/backups" ]; then
        find "${DEPLOY_DIR}/backups" -name "*.tar.gz" -type f -mtime +7 -delete 2>/dev/null || true
        log_success "Old backups cleaned"
    else
        log_warning "No backup directory found"
    fi
}

cleanup_temp_files() {
    log "Cleaning temporary files..."
    
    find /tmp -name "scanifyme-*" -type f -mtime +1 -delete 2>/dev/null || true
    find /tmp -name "css_backend" -type d -mtime +1 -exec rm -rf {} + 2>/dev/null || true
    find /tmp -name "js_backend" -type d -mtime +1 -exec rm -rf {} + 2>/dev/null || true
    find /tmp -name "cookies.txt" -type f -mtime +1 -delete 2>/dev/null || true
    
    log_success "Temporary files cleaned"
}

check_docker_safe() {
    local containers_running=$(docker ps -q | wc -l)
    
    if [ "$containers_running" -eq 0 ]; then
        log_warning "No containers running - cleanup will proceed"
        return 0
    fi
    
    local scanifyme_running=$(docker ps --format '{{.Names}}' | grep -c scanifyme || echo "0")
    
    if [ "$scanifyme_running" -lt 5 ]; then
        log_warning "Some ScanifyMe containers not running - check before cleanup"
        return 1
    fi
    
    return 0
}

main() {
    local command="${1:-safe}"
    
    echo "=========================================="
    echo "  ScanifyMe Cleanup Script"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=========================================="
    
    show_disk_status
    
    case "$command" in
        safe)
            log "Running SAFE cleanup (no volume prune)..."
            cleanup_docker_images
            cleanup_docker_containers
            cleanup_docker_networks
            cleanup_docker_build_cache
            cleanup_deploy_logs
            cleanup_temp_files
            ;;
        full)
            log "Running FULL cleanup..."
            cleanup_docker_images
            cleanup_docker_containers
            cleanup_docker_networks
            cleanup_docker_build_cache
            cleanup_deploy_logs
            cleanup_old_backups
            cleanup_temp_files
            ;;
        docker)
            log "Running Docker-only cleanup..."
            cleanup_docker_images
            cleanup_docker_containers
            cleanup_docker_networks
            cleanup_docker_build_cache
            ;;
        logs)
            log "Running logs-only cleanup..."
            cleanup_deploy_logs
            cleanup_temp_files
            ;;
        help|*)
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  safe    - Safe cleanup (default, no volume prune)"
            echo "  full    - Full cleanup including old backups"
            echo "  docker  - Docker-only cleanup"
            echo "  logs    - Logs-only cleanup"
            echo "  help    - Show this help"
            echo ""
            echo "Examples:"
            echo "  $0          # Safe cleanup"
            echo "  $0 safe     # Safe cleanup"
            echo "  $0 full     # Full cleanup (removes old backups)"
            echo "  $0 docker   # Docker cleanup only"
            echo ""
            exit 0
            ;;
    esac
    
    echo ""
    show_disk_status
    
    log_success "Cleanup complete"
}

main "$@"
