#!/bin/bash
set -euo pipefail

DEPLOY_DIR="/opt/scanifyme"
SITE_NAME="scanifyme.app"
API_URL="http://localhost:8080"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

section() {
    echo ""
    echo -e "${BLUE}━━━ $1 ━━━${NC}"
}

main() {
    echo "┌─────────────────────────────────────────┐"
    echo "│       ScanifyMe Status Summary          │"
    echo "│       $(date '+%Y-%m-%d %H:%M:%S')           │"
    echo "└─────────────────────────────────────────┘"

    section "System Resources"
    
    local disk_avail=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
    local disk_used=$(df -h / | tail -1 | awk '{print $5}')
    local mem_avail=$(free -m | awk '/^Mem:/{print $7}')
    local mem_total=$(free -m | awk '/^Mem:/{print $2}')
    local load=$(uptime | awk -F'load average:' '{print $2}' | xargs)
    
    if [ "$disk_avail" -lt 5 ]; then
        echo -e "  Disk: ${RED}${disk_avail}GB available (${disk_used} used)${NC}"
    elif [ "$disk_avail" -lt 10 ]; then
        echo -e "  Disk: ${YELLOW}${disk_avail}GB available (${disk_used} used)${NC}"
    else
        echo -e "  Disk: ${GREEN}${disk_avail}GB available (${disk_used} used)${NC}"
    fi
    
    if [ "$mem_avail" -lt 500 ]; then
        echo -e "  Memory: ${RED}${mem_avail}MB available / ${mem_total}MB total${NC}"
    elif [ "$mem_avail" -lt 1000 ]; then
        echo -e "  Memory: ${YELLOW}${mem_avail}MB available / ${mem_total}MB total${NC}"
    else
        echo -e "  Memory: ${GREEN}${mem_avail}MB available / ${mem_total}MB total${NC}"
    fi
    
    echo "  Load: $load"

    section "Containers"
    
    local total_containers=0
    local running_containers=0
    local unhealthy_containers=""
    
    for container in scanifyme-backend-1 scanifyme-frontend-1 scanifyme-db-1 scanifyme-redis-cache-1 scanifyme-redis-queue-1 scanifyme-websocket-1 scanifyme-queue-short-1 scanifyme-queue-long-1 scanifyme-scheduler-1; do
        ((total_containers++)) || true
        
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            ((running_containers++)) || true
            local health=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$container" 2>/dev/null || echo "unknown")
            
            if [ "$health" = "unhealthy" ]; then
                unhealthy_containers="${unhealthy_containers} ${container}"
            fi
        fi
    done
    
    if [ "$running_containers" -eq "$total_containers" ]; then
        echo -e "  Status: ${GREEN}${running_containers}/${total_containers} running${NC}"
    else
        echo -e "  Status: ${RED}${running_containers}/${total_containers} running${NC}"
    fi
    
    if [ -n "$unhealthy_containers" ]; then
        echo -e "  Unhealthy: ${RED}${unhealthy_containers}${NC}"
    fi

    section "Services"
    
    local api_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "${API_URL}/api/method/ping" 2>/dev/null || echo "000")
    local frontend_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "${API_URL}/frontend" 2>/dev/null || echo "000")
    
    if [ "$api_status" = "200" ]; then
        echo -e "  API: ${GREEN}✓ OK (HTTP $api_status)${NC}"
    else
        echo -e "  API: ${RED}✗ FAIL (HTTP $api_status)${NC}"
    fi
    
    if [ "$frontend_status" = "200" ]; then
        echo -e "  Frontend: ${GREEN}✓ OK (HTTP $frontend_status)${NC}"
    else
        echo -e "  Frontend: ${RED}✗ FAIL (HTTP $frontend_status)${NC}"
    fi

    section "Database"
    
    if docker exec scanifyme-db-1 mariadb-admin ping -u root -pScanifyMe2026SecureDB --silent 2>/dev/null; then
        local db_size=$(docker exec scanifyme-db-1 mariadb -u root -pScanifyMe2026SecureDB -e "SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) FROM information_schema.tables WHERE table_schema='scanifyme';" 2>/dev/null | tail -1)
        echo -e "  MariaDB: ${GREEN}✓ Responsive${NC}"
        echo "  Size: ${db_size}MB"
    else
        echo -e "  MariaDB: ${RED}✗ Not responsive${NC}"
    fi

    section "Backups"
    
    if [ -d "${DEPLOY_DIR}/backups" ]; then
        local backup_count=$(find "${DEPLOY_DIR}/backups" -name "*.tar.gz" -type f 2>/dev/null | wc -l)
        local backup_size=$(du -sh "${DEPLOY_DIR}/backups" 2>/dev/null | cut -f1)
        
        echo "  Directory: ${DEPLOY_DIR}/backups"
        echo "  Count: $backup_count"
        echo "  Size: $backup_size"
        
        if [ "$backup_count" -gt 0 ]; then
            local latest=$(find "${DEPLOY_DIR}/backups" -name "*.tar.gz" -type f -printf "%Tc\n" 2>/dev/null | sort -r | head -1)
            echo "  Latest: $latest"
        fi
    else
        echo -e "  ${YELLOW}No backup directory found${NC}"
    fi

    section "Docker Resources"
    
    local images_count=$(docker images -q | wc -l)
    local dangling=$(docker images -f "dangling=true" -q | wc -l)
    local volumes=$(docker volume ls -q | wc -l)
    
    echo "  Images: $images_count"
    
    if [ "$dangling" -gt 0 ]; then
        echo -e "  Dangling: ${YELLOW}$dangling (run cleanup recommended)${NC}"
    else
        echo -e "  Dangling: ${GREEN}none${NC}"
    fi
    
    echo "  Volumes: $volumes"

    section "Recent Activity"
    
    local latest_log=$(ls -t /tmp/scanifyme-deploy-*.log 2>/dev/null | head -1)
    if [ -n "$latest_log" ]; then
        local log_date=$(basename "$latest_log" | sed 's/scanifyme-deploy-//;s/.log//')
        echo "  Last deploy: $log_date"
        
        local result=$(tail -5 "$latest_log" 2>/dev/null | grep -i "success\|fail\|error" | head -1)
        if [ -n "$result" ]; then
            echo "  Result: $result"
        fi
    else
        echo "  No deployment logs found"
    fi

    echo ""
    echo "┌─────────────────────────────────────────┐"
    echo "│  Quick Commands:                        │"
    echo "│  ./deploy/healthcheck.sh  - Full check  │"
    echo "│  ./deploy/diagnostics.sh  - Debug info  │"
    echo "│  ./deploy/backup.sh create - Backup     │"
    echo "│  ./deploy/cleanup.sh      - Free space  │"
    echo "└─────────────────────────────────────────┘"
    echo ""
}

main
