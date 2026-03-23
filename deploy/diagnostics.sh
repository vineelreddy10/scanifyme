#!/bin/bash
set -euo pipefail

DEPLOY_DIR="/opt/scanifyme"
SITE_NAME="scanifyme.app"
API_URL="http://localhost:8080"
LOG_TAIL_LINES=50

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

section() {
    echo ""
    echo -e "${BLUE}========== $1 ==========${NC}"
    echo ""
}

subsection() {
    echo -e "${YELLOW}--- $1 ---${NC}"
}

main() {
    echo "=========================================="
    echo "  ScanifyMe Diagnostics Report"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=========================================="

    section "SYSTEM RESOURCES"
    
    subsection "Disk Usage"
    df -h / | head -2
    echo ""
    echo "Deploy directory size:"
    du -sh /opt/scanifyme 2>/dev/null || echo "  Not available"
    
    subsection "Memory Usage"
    free -h
    
    subsection "CPU Load"
    uptime

    section "DOCKER STATUS"
    
    subsection "Running Containers"
    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep scanifyme || echo "  No scanifyme containers found"
    
    subsection "Container Resource Usage"
    docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}' | grep scanifyme || echo "  No stats available"
    
    subsection "Docker Disk Usage"
    docker system df

    section "CONTAINER LOGS (Last $LOG_TAIL_LINES lines)"
    
    for container in scanifyme-backend-1 scanifyme-frontend-1 scanifyme-db-1; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            subsection "$container logs"
            docker logs --tail "$LOG_TAIL_LINES" "$container" 2>&1 | tail -20
        fi
    done

    section "APPLICATION HEALTH"
    
    subsection "API Ping"
    curl -s "${API_URL}/api/method/ping" 2>/dev/null || echo "  API not responding"
    
    subsection "Frontend Check"
    local frontend_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${API_URL}/frontend" 2>/dev/null || echo "000")
    echo "  HTTP Status: $frontend_status"
    
    subsection "Login Endpoint"
    local login_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${API_URL}/api/method/login" 2>/dev/null || echo "000")
    echo "  HTTP Status: $login_status"

    section "DATABASE STATUS"
    
    if docker ps --format '{{.Names}}' | grep -q "scanifyme-db-1"; then
        subsection "MariaDB Status"
        docker exec scanifyme-db-1 mariadb-admin ping -u root -pScanifyMe2026SecureDB --silent 2>/dev/null && echo "  MariaDB: Responsive" || echo "  MariaDB: Not responsive"
        
        subsection "Database Size"
        docker exec scanifyme-db-1 mariadb -u root -pScanifyMe2026SecureDB -e "SELECT table_schema AS 'Database', ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) AS 'Size (MB)' FROM information_schema.tables GROUP BY table_schema;" 2>/dev/null || echo "  Could not retrieve database size"
        
        subsection "Table Count"
        docker exec scanifyme-db-1 mariadb -u root -pScanifyMe2026SecureDB scanifyme -e "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema='scanifyme';" 2>/dev/null || echo "  Could not retrieve table count"
    else
        echo "  Database container not running"
    fi

    section "REDIS STATUS"
    
    if docker ps --format '{{.Names}}' | grep -q "scanifyme-redis-cache-1"; then
        subsection "Cache Redis"
        docker exec scanifyme-redis-cache-1 redis-cli info server 2>/dev/null | grep redis_version || echo "  Not responsive"
    fi
    
    if docker ps --format '{{.Names}}' | grep -q "scanifyme-redis-queue-1"; then
        subsection "Queue Redis"
        docker exec scanifyme-redis-queue-1 redis-cli info server 2>/dev/null | grep redis_version || echo "  Not responsive"
    fi

    section "DEPLOYMENT FILES"
    
    subsection "apps.json"
    cat "${DEPLOY_DIR}/apps.json" 2>/dev/null || echo "  Not found"
    
    subsection "Environment File"
    if [ -f "${DEPLOY_DIR}/.env" ]; then
        echo "  File exists ($(wc -l < ${DEPLOY_DIR}/.env) lines)"
        grep -E "^(FRAPPE_VERSION|SITE_NAME|HTTP_PORT)" "${DEPLOY_DIR}/.env" 2>/dev/null || echo "  Could not read key variables"
    else
        echo "  Not found"
    fi
    
    subsection "Compose File"
    if [ -f "${DEPLOY_DIR}/compose.prod.yaml" ]; then
        echo "  File exists"
    else
        echo "  Not found"
    fi

    section "RECENT DEPLOYMENT LOGS"
    
    subsection "Latest Deploy Log"
    local latest_log=$(ls -t /tmp/scanifyme-deploy-*.log 2>/dev/null | head -1)
    if [ -n "$latest_log" ]; then
        echo "  Log file: $latest_log"
        echo "  Last 20 lines:"
        tail -20 "$latest_log"
    else
        echo "  No deployment logs found"
    fi

    section "NETWORK CONNECTIVITY"
    
    subsection "Port 8080"
    if netstat -tlnp 2>/dev/null | grep -q ":8080"; then
        echo "  Port 8080: LISTENING"
    else
        echo "  Port 8080: NOT LISTENING"
    fi
    
    subsection "Container Network"
    docker network ls | grep scanifyme || echo "  No scanifyme networks found"

    section "BACKUPS"
    
    subsection "Backup Directory"
    if [ -d "${DEPLOY_DIR}/backups" ]; then
        local backup_count=$(find "${DEPLOY_DIR}/backups" -name "*.tar.gz" -type f | wc -l)
        echo "  Directory exists"
        echo "  Backup count: $backup_count"
        if [ "$backup_count" -gt 0 ]; then
            echo "  Latest backup:"
            find "${DEPLOY_DIR}/backups" -name "*.tar.gz" -type f -printf "%Tc %p\n" | sort -r | head -1
        fi
    else
        echo "  No backup directory found"
    fi

    section "COMMON ISSUES CHECK"
    
    subsection "Restart Loops"
    local restart_issues=0
    for container in $(docker ps --format '{{.Names}}' | grep scanifyme); do
        local restarts=$(docker inspect --format '{{.RestartCount}}' "$container" 2>/dev/null || echo "0")
        if [ "$restarts" -gt 5 ]; then
            echo "  WARNING: $container has restarted $restarts times"
            restart_issues=1
        fi
    done
    if [ "$restart_issues" -eq 0 ]; then
        echo "  No restart loops detected"
    fi
    
    subsection "High Memory Containers"
    docker stats --no-stream --format '{{.Name}}\t{{.MemPerc}}' | grep scanifyme | awk -F'\t' '{gsub(/%/,"",$2); if($2+0 > 80) print "  WARNING: "$1" using "$2"% memory"}' || echo "  No high memory usage detected"
    
    subsection "Disk Pressure"
    local disk_avail=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$disk_avail" -lt 5 ]; then
        echo "  CRITICAL: Only ${disk_avail}GB available"
    elif [ "$disk_avail" -lt 10 ]; then
        echo "  WARNING: Only ${disk_avail}GB available"
    else
        echo "  OK: ${disk_avail}GB available"
    fi

    echo ""
    echo "=========================================="
    echo "  Diagnostics Complete"
    echo "=========================================="
}

main
