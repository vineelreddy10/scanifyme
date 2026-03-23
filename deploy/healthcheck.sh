#!/bin/bash
set -euo pipefail

DEPLOY_DIR="/opt/scanifyme"
SITE_NAME="scanifyme.app"
API_URL="http://localhost:8080"
MIN_DISK_GB=5
MIN_MEMORY_MB=500

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

STATUS_OK=0
STATUS_WARNING=1
STATUS_CRITICAL=2

overall_status=$STATUS_OK

log_ok() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
    if [ $overall_status -lt $STATUS_WARNING ]; then
        overall_status=$STATUS_WARNING
    fi
}

log_critical() {
    echo -e "${RED}[✗]${NC} $1"
    overall_status=$STATUS_CRITICAL
}

check_containers() {
    echo "Container Status:"
    
    local containers=(
        "scanifyme-backend-1"
        "scanifyme-frontend-1"
        "scanifyme-db-1"
        "scanifyme-redis-cache-1"
        "scanifyme-redis-queue-1"
        "scanifyme-websocket-1"
        "scanifyme-queue-short-1"
        "scanifyme-queue-long-1"
        "scanifyme-scheduler-1"
    )
    
    for container in "${containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            local status=$(docker inspect --format '{{.State.Status}}' "$container" 2>/dev/null || echo "unknown")
            local restarts=$(docker inspect --format '{{.RestartCount}}' "$container" 2>/dev/null || echo "0")
            
            if [ "$status" = "running" ]; then
                if [ "$restarts" -gt 5 ]; then
                    log_warning "  $container: running but $restarts restarts detected"
                else
                    log_ok "  $container: running"
                fi
            else
                log_critical "  $container: $status"
            fi
        else
            log_critical "  $container: not found"
        fi
    done
    echo ""
}

check_disk() {
    echo "Disk Usage:"
    
    local available_disk=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
    local used_percent=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ "$available_disk" -lt "$MIN_DISK_GB" ]; then
        log_critical "  Root: ${available_disk}GB available (${used_percent}% used) - CRITICAL"
    elif [ "$available_disk" -lt 10 ]; then
        log_warning "  Root: ${available_disk}GB available (${used_percent}% used) - WARNING"
    else
        log_ok "  Root: ${available_disk}GB available (${used_percent}% used)"
    fi
    
    if [ -d "/opt/scanifyme" ]; then
        local deploy_size=$(du -sh /opt/scanifyme 2>/dev/null | cut -f1)
        log_ok "  Deploy dir: $deploy_size"
    fi
    echo ""
}

check_memory() {
    echo "Memory Usage:"
    
    local total_mem=$(free -m | awk '/^Mem:/{print $2}')
    local available_mem=$(free -m | awk '/^Mem:/{print $7}')
    local used_percent=$((100 - (available_mem * 100 / total_mem)))
    
    if [ "$available_mem" -lt "$MIN_MEMORY_MB" ]; then
        log_critical "  RAM: ${available_mem}MB available (${used_percent}% used) - CRITICAL"
    elif [ "$available_mem" -lt 1000 ]; then
        log_warning "  RAM: ${available_mem}MB available (${used_percent}% used) - WARNING"
    else
        log_ok "  RAM: ${available_mem}MB available (${used_percent}% used)"
    fi
    echo ""
}

check_api() {
    echo "API Health:"
    
    local ping_response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${API_URL}/api/method/ping" 2>/dev/null || echo "000")
    
    if [ "$ping_response" = "200" ]; then
        log_ok "  /api/method/ping: HTTP $ping_response"
    else
        log_critical "  /api/method/ping: HTTP $ping_response"
    fi
    
    local frontend_response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${API_URL}/frontend" 2>/dev/null || echo "000")
    
    if [ "$frontend_response" = "200" ]; then
        log_ok "  /frontend: HTTP $frontend_response"
    else
        log_critical "  /frontend: HTTP $frontend_response"
    fi
    echo ""
}

check_database() {
    echo "Database:"
    
    if docker exec scanifyme-db-1 mariadb-admin ping -u root -pScanifyMe2026SecureDB --silent 2>/dev/null; then
        log_ok "  MariaDB: responsive"
        
        local db_size=$(docker exec scanifyme-db-1 mariadb -u root -pScanifyMe2026SecureDB -e "SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) AS 'DB Size in MB' FROM information_schema.tables WHERE table_schema='scanifyme';" 2>/dev/null | tail -1)
        log_ok "  Database size: ${db_size}MB"
    else
        log_critical "  MariaDB: not responsive"
    fi
    echo ""
}

check_redis() {
    echo "Redis:"
    
    if docker exec scanifyme-redis-cache-1 redis-cli ping 2>/dev/null | grep -q "PONG"; then
        log_ok "  Cache: responsive"
    else
        log_warning "  Cache: not responsive"
    fi
    
    if docker exec scanifyme-redis-queue-1 redis-cli ping 2>/dev/null | grep -q "PONG"; then
        log_ok "  Queue: responsive"
    else
        log_warning "  Queue: not responsive"
    fi
    echo ""
}

check_docker_resources() {
    echo "Docker Resources:"
    
    local images_count=$(docker images -q | wc -l)
    local images_size=$(docker system df --format '{{.Size}}' | head -1)
    log_ok "  Images: $images_count ($images_size)"
    
    local volumes_count=$(docker volume ls -q | wc -l)
    log_ok "  Volumes: $volumes_count"
    
    local dangling=$(docker images -f "dangling=true" -q | wc -l)
    if [ "$dangling" -gt 0 ]; then
        log_warning "  Dangling images: $dangling (cleanup recommended)"
    else
        log_ok "  Dangling images: none"
    fi
    echo ""
}

main() {
    echo "=========================================="
    echo "  ScanifyMe Health Check"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=========================================="
    echo ""
    
    check_containers
    check_disk
    check_memory
    check_api
    check_database
    check_redis
    check_docker_resources
    
    echo "=========================================="
    case $overall_status in
        $STATUS_OK)
            echo -e "  Overall Status: ${GREEN}HEALTHY${NC}"
            ;;
        $STATUS_WARNING)
            echo -e "  Overall Status: ${YELLOW}WARNING${NC}"
            ;;
        $STATUS_CRITICAL)
            echo -e "  Overall Status: ${RED}CRITICAL${NC}"
            ;;
    esac
    echo "=========================================="
    
    exit $overall_status
}

main
