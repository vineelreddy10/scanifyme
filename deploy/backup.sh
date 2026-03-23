#!/bin/bash
set -uo pipefail

DEPLOY_DIR="/opt/scanifyme"
SITE_NAME="scanifyme.app"
BACKUP_DIR="/opt/scanifyme/backups"
RETENTION_DAYS=7
MAX_BACKUPS=10
MIN_DISK_GB=5
DB_NAME="_af4aa012b6d4faf1"

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

preflight_checks() {
    log "Running preflight checks..."
    
    if [ "$EUID" -ne 0 ]; then 
        log_error "Please run as root or with sudo"
        return 1
    fi
    
    if [ ! -d "$DEPLOY_DIR" ]; then
        log_error "Deployment directory $DEPLOY_DIR does not exist"
        return 1
    fi
    
    if ! docker ps &> /dev/null; then
        log_error "Docker is not running"
        return 1
    fi
    
    if ! docker ps | grep -q "scanifyme-db-1"; then
        log_error "Database container is not running"
        return 1
    fi
    
    local available_disk=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$available_disk" -lt "$MIN_DISK_GB" ]; then
        log_error "Insufficient disk space: ${available_disk}GB available, ${MIN_DISK_GB}GB required"
        return 1
    fi
    log_success "Disk space OK: ${available_disk}GB available"
    
    mkdir -p "$BACKUP_DIR"
    
    log_success "Preflight checks passed"
    return 0
}

create_backup() {
    log "Creating backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="scanifyme_backup_${timestamp}"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    mkdir -p "$backup_path"
    
    log "Creating database backup..."
    if docker exec scanifyme-db-1 mariadb-dump -u root -pScanifyMe2026SecureDB "$DB_NAME" > "${backup_path}/database.sql" 2>/dev/null; then
        if [ -f "${backup_path}/database.sql" ] && [ -s "${backup_path}/database.sql" ]; then
            log_success "Database backup created: $(du -h ${backup_path}/database.sql | cut -f1)"
        else
            log_error "Database backup file is empty"
            rm -rf "$backup_path"
            return 1
        fi
    else
        log_error "Database backup failed"
        rm -rf "$backup_path"
        return 1
    fi
    
    log "Creating site config backup..."
    if docker cp scanifyme-backend-1:/home/frappe/frappe-bench/sites/scanifyme.app/site_config.json "${backup_path}/site_config.json" 2>/dev/null; then
        log_success "Site config backup created"
    else
        log_warning "Site config backup failed (non-critical)"
    fi
    
    log "Creating environment backup..."
    if [ -f "${DEPLOY_DIR}/.env" ]; then
        cp "${DEPLOY_DIR}/.env" "${backup_path}/env.backup"
        log_success "Environment file backed up"
    fi
    
    log "Creating apps.json backup..."
    if [ -f "${DEPLOY_DIR}/apps.json" ]; then
        cp "${DEPLOY_DIR}/apps.json" "${backup_path}/apps.json"
        log_success "apps.json backed up"
    fi
    
    log "Creating backup manifest..."
    cat > "${backup_path}/manifest.txt" << EOF
Backup Created: $(date)
Site Name: ${SITE_NAME}
Database Size: $(du -h ${backup_path}/database.sql | cut -f1)
Backup Contents:
- database.sql (MariaDB dump)
- site_config.json (site configuration)
- env.backup (environment variables)
- apps.json (app configuration)
EOF
    
    log "Compressing backup..."
    cd "$BACKUP_DIR"
    if tar -czf "${backup_name}.tar.gz" "$backup_name"; then
        rm -rf "$backup_name"
        log_success "Backup compressed: ${backup_name}.tar.gz ($(du -h ${backup_name}.tar.gz | cut -f1))"
    else
        log_error "Backup compression failed"
        return 1
    fi
    
    log_success "Backup created successfully: ${BACKUP_DIR}/${backup_name}.tar.gz"
    return 0
}

list_backups() {
    log "Available backups:"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        log_warning "No backup directory found"
        return 0
    fi
    
    local backup_count=$(find "$BACKUP_DIR" -name "*.tar.gz" -type f | wc -l)
    
    if [ "$backup_count" -eq 0 ]; then
        log_warning "No backups found"
        return 0
    fi
    
    echo ""
    echo "Backup Directory: $BACKUP_DIR"
    echo "Total Backups: $backup_count"
    echo ""
    echo "Available Backups:"
    echo "----------------------------------------"
    
    find "$BACKUP_DIR" -name "*.tar.gz" -type f -printf "%T@ %p\n" | sort -rn | while read line; do
        local filepath=$(echo "$line" | awk '{print $2}')
        local filename=$(basename "$filepath")
        local size=$(du -h "$filepath" | cut -f1)
        local date=$(stat -c "%y" "$filepath" | cut -d'.' -f1)
        echo "  $filename ($size) - $date"
    done
    
    echo ""
    return 0
}

cleanup_old_backups() {
    log "Cleaning old backups..."
    
    if [ ! -d "$BACKUP_DIR" ]; then
        log_warning "No backup directory found"
        return 0
    fi
    
    find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
    
    local backup_count=$(find "$BACKUP_DIR" -name "*.tar.gz" -type f | wc -l)
    
    if [ "$backup_count" -gt "$MAX_BACKUPS" ]; then
        local excess=$((backup_count - MAX_BACKUPS))
        log "Removing $excess excess backups (keeping $MAX_BACKUPS most recent)"
        
        find "$BACKUP_DIR" -name "*.tar.gz" -type f -printf "%T@ %p\n" | sort -n | head -n "$excess" | while read line; do
            local filepath=$(echo "$line" | awk '{print $2}')
            log "Removing: $(basename $filepath)"
            rm -f "$filepath"
        done
    fi
    
    local remaining=$(find "$BACKUP_DIR" -name "*.tar.gz" -type f | wc -l)
    log_success "Cleanup complete. $remaining backups remaining"
    
    return 0
}

show_backup_info() {
    log "Backup information:"
    
    echo ""
    echo "Backup Configuration:"
    echo "  Backup Directory: $BACKUP_DIR"
    echo "  Retention Days: $RETENTION_DAYS"
    echo "  Max Backups: $MAX_BACKUPS"
    echo "  Min Disk Required: ${MIN_DISK_GB}GB"
    echo ""
    
    if [ -d "$BACKUP_DIR" ]; then
        local backup_count=$(find "$BACKUP_DIR" -name "*.tar.gz" -type f | wc -l)
        local total_size=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
        
        echo "Current Status:"
        echo "  Total Backups: $backup_count"
        echo "  Total Size: $total_size"
        echo ""
        
        if [ "$backup_count" -gt 0 ]; then
            echo "Most Recent Backup:"
            find "$BACKUP_DIR" -name "*.tar.gz" -type f -printf "%T@ %Tc %p\n" | sort -rn | head -1 | while read line; do
                local date=$(echo "$line" | awk '{print $2, $3, $4, $5, $6}')
                local filepath=$(echo "$line" | awk '{print $7}')
                local filename=$(basename "$filepath")
                local size=$(du -h "$filepath" | cut -f1)
                echo "  $filename ($size) - $date"
            done
        fi
    else
        echo "Current Status: No backups created yet"
    fi
    
    echo ""
    return 0
}

main() {
    local command="${1:-help}"
    
    case "$command" in
        create)
            preflight_checks && create_backup
            ;;
        list)
            list_backups
            ;;
        cleanup)
            cleanup_old_backups
            ;;
        info)
            show_backup_info
            ;;
        help|*)
            echo "ScanifyMe Backup Script"
            echo ""
            echo "Usage: $0 <command>"
            echo ""
            echo "Commands:"
            echo "  create   - Create a new backup"
            echo "  list     - List available backups"
            echo "  cleanup  - Remove old backups (older than ${RETENTION_DAYS} days)"
            echo "  info     - Show backup configuration and status"
            echo "  help     - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 create      # Create a new backup"
            echo "  $0 list        # List all backups"
            echo "  $0 cleanup     # Clean up old backups"
            echo ""
            ;;
    esac
}

main "$@"
