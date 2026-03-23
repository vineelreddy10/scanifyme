#!/bin/bash
set -euo pipefail

# ============================================================
# ScanifyMe Deployment Script
# Safe, repeatable deployment for low-resource VPS
# ============================================================

# Configuration
DEPLOY_DIR="/opt/scanifyme"
SITE_NAME="scanifyme.app"
COMPOSE_FILE="compose.prod.yaml"
ENV_FILE=".env"
IMAGE_TAG="scanifyme:v16"
MIN_DISK_GB=10
LOG_FILE="/tmp/scanifyme-deploy-$(date +%Y%m%d-%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" | tee -a "$LOG_FILE"
}

# ============================================================
# PREFLIGHT CHECKS
# ============================================================

preflight_checks() {
    log "========== PREFLIGHT CHECKS =========="
    
    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ]; then 
        log_error "Please run as root or with sudo"
        return 1
    fi
    
    # Check deployment directory exists
    if [ ! -d "$DEPLOY_DIR" ]; then
        log_error "Deployment directory $DEPLOY_DIR does not exist"
        return 1
    fi
    log_success "Deployment directory exists: $DEPLOY_DIR"
    
    # Check Docker is available
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        return 1
    fi
    log_success "Docker is available"
    
    # Check Docker Compose is available
    if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not available"
        return 1
    fi
    log_success "Docker Compose is available"
    
    # Check required files exist
    cd "$DEPLOY_DIR"
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Compose file $COMPOSE_FILE not found"
        return 1
    fi
    log_success "Compose file exists: $COMPOSE_FILE"
    
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file $ENV_FILE not found"
        return 1
    fi
    log_success "Environment file exists: $ENV_FILE"
    
    if [ ! -f "apps.json" ]; then
        log_error "apps.json not found"
        return 1
    fi
    log_success "apps.json exists"
    
    # Check disk space
    local available_disk=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$available_disk" -lt "$MIN_DISK_GB" ]; then
        log_error "Insufficient disk space: ${available_disk}GB available, ${MIN_DISK_GB}GB required"
        return 1
    fi
    log_success "Disk space OK: ${available_disk}GB available"
    
    # Check Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        return 1
    fi
    log_success "Docker daemon is running"
    
    # Check if containers are in known state
    local running_containers=$(docker ps -q | wc -l)
    log "Running containers: $running_containers"
    
    log_success "All preflight checks passed"
    return 0
}

# ============================================================
# LOW-RESOURCE CLEANUP
# ============================================================

cleanup_docker() {
    log "========== DOCKER CLEANUP =========="
    
    # Remove dangling images
    log "Removing dangling images..."
    docker image prune -f 2>&1 | tee -a "$LOG_FILE"
    
    # Remove stopped containers
    log "Removing stopped containers..."
    docker container prune -f 2>&1 | tee -a "$LOG_FILE"
    
    # Remove unused networks
    log "Removing unused networks..."
    docker network prune -f 2>&1 | tee -a "$LOG_FILE"
    
    # Remove build cache
    log "Removing build cache..."
    docker builder prune -a -f 2>&1 | tee -a "$LOG_FILE"
    
    # DO NOT remove volumes - this would delete database!
    log_warning "Skipping volume cleanup (would delete database)"
    
    # Check disk after cleanup
    local available_disk=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
    log_success "Disk cleanup complete: ${available_disk}GB available"
}

# ============================================================
# BUILD AND DEPLOY
# ============================================================

build_image() {
    log "========== BUILDING DOCKER IMAGE =========="
    
    cd "$DEPLOY_DIR"
    
    # Build the image
    log "Building custom image with latest code from GitHub..."
    docker build \
        --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
        --build-arg=FRAPPE_BRANCH=version-16 \
        --build-arg=APPS_JSON_BASE64=$(base64 -w 0 apps.json) \
        --tag="$IMAGE_TAG" \
        --file=images/custom/Containerfile . \
        --load 2>&1 | tee -a "$LOG_FILE"
    
    if [ $? -ne 0 ]; then
        log_error "Image build failed"
        return 1
    fi
    
    log_success "Image built successfully: $IMAGE_TAG"
}

restart_services() {
    log "========== RESTARTING SERVICES =========="
    
    cd "$DEPLOY_DIR"
    
    # Restart containers
    log "Restarting containers..."
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d 2>&1 | tee -a "$LOG_FILE"
    
    if [ $? -ne 0 ]; then
        log_error "Failed to restart services"
        return 1
    fi
    
    # Wait for services to be healthy
    log "Waiting for services to start..."
    sleep 10
    
    log_success "Services restarted"
}

run_migrations() {
    log "========== RUNNING MIGRATIONS =========="
    
    # Run migrations
    log "Running database migrations..."
    docker exec scanifyme-backend-1 bench --site "$SITE_NAME" migrate 2>&1 | tee -a "$LOG_FILE"
    
    if [ $? -ne 0 ]; then
        log_error "Migration failed"
        return 1
    fi
    
    log_success "Migrations completed"
}

build_assets() {
    log "========== BUILDING ASSETS =========="
    
    # Build frontend assets
    log "Building frontend assets..."
    docker exec scanifyme-backend-1 bench --site "$SITE_NAME" build 2>&1 | tee -a "$LOG_FILE"
    
    if [ $? -ne 0 ]; then
        log_warning "Asset build had issues (may be non-critical)"
    fi
    
    log_success "Assets built"
}

sync_assets() {
    log "========== SYNCING ASSETS TO FRONTEND =========="
    
    # Copy CSS files from backend to frontend
    log "Syncing CSS files..."
    docker cp scanifyme-backend-1:/home/frappe/frappe-bench/sites/assets/frappe/dist/css/. /tmp/css_backend/ 2>&1 | tee -a "$LOG_FILE"
    docker cp /tmp/css_backend/. scanifyme-frontend-1:/home/frappe/frappe-bench/sites/assets/frappe/dist/css/ 2>&1 | tee -a "$LOG_FILE"
    
    # Copy JS files
    log "Syncing JS files..."
    docker cp scanifyme-backend-1:/home/frappe/frappe-bench/sites/assets/frappe/dist/js/. /tmp/js_backend/ 2>&1 | tee -a "$LOG_FILE"
    docker cp /tmp/js_backend/. scanifyme-frontend-1:/home/frappe/frappe-bench/sites/assets/frappe/dist/js/ 2>&1 | tee -a "$LOG_FILE"
    
    log_success "Assets synced"
}

clear_caches() {
    log "========== CLEARING CACHES =========="
    
    # Clear application cache
    log "Clearing application cache..."
    docker exec scanifyme-backend-1 bench --site "$SITE_NAME" clear-cache 2>&1 | tee -a "$LOG_FILE"
    
    # Clear website cache
    log "Clearing website cache..."
    docker exec scanifyme-backend-1 bench --site "$SITE_NAME" clear-website-cache 2>&1 | tee -a "$LOG_FILE"
    
    log_success "Caches cleared"
}

# ============================================================
# POST-DEPLOY SMOKE TESTS
# ============================================================

smoke_tests() {
    log "========== POST-DEPLOY SMOKE TESTS =========="
    
    local failed=0
    
    # Test 1: API Ping
    log "Test 1: API Ping..."
    if curl -s http://localhost:8080/api/method/ping | grep -q "pong"; then
        log_success "API Ping: PASS"
    else
        log_error "API Ping: FAIL"
        failed=1
    fi
    
    # Test 2: Frontend loads
    log "Test 2: Frontend loads..."
    if curl -s http://localhost:8080/frontend | grep -q "doctype html"; then
        log_success "Frontend load: PASS"
    else
        log_error "Frontend load: FAIL"
        failed=1
    fi
    
    # Test 3: Login works
    log "Test 3: Login works..."
    local login_response=$(curl -s -c /tmp/smoke_cookies.txt -X POST http://localhost:8080/api/method/login \
        -H 'Content-Type: application/json' \
        -d '{"usr":"Administrator","pwd":"admin@123"}')
    if echo "$login_response" | grep -q "Logged In"; then
        log_success "Login: PASS"
    else
        log_error "Login: FAIL"
        failed=1
    fi
    
    # Test 4: QR Batch list API
    log "Test 4: QR Batch list API..."
    local batch_response=$(curl -s -b /tmp/smoke_cookies.txt -X POST \
        http://localhost:8080/api/method/scanifyme.api.safe_list_api.get_safe_list_rows \
        -H 'Content-Type: application/json' \
        -d '{"doctype":"QR Batch"}')
    if echo "$batch_response" | grep -q "rows"; then
        log_success "QR Batch list: PASS"
    else
        log_error "QR Batch list: FAIL"
        failed=1
    fi
    
    # Test 5: Filtered QR Code Tag list API
    log "Test 5: Filtered QR Code Tag list..."
    local tags_response=$(curl -s -b /tmp/smoke_cookies.txt -X POST \
        http://localhost:8080/api/method/scanifyme.api.safe_list_api.get_safe_list_rows \
        -H 'Content-Type: application/json' \
        -d '{"doctype":"QR Code Tag","filters":{"batch":"QRB-2026-00001"}}')
    if echo "$tags_response" | grep -q "rows"; then
        log_success "Filtered QR list: PASS"
    else
        log_error "Filtered QR list: FAIL"
        failed=1
    fi
    
    # Test 6: Owner dashboard API
    log "Test 6: Owner dashboard API..."
    local dashboard_response=$(curl -s -b /tmp/smoke_cookies.txt -X POST \
        http://localhost:8080/api/method/scanifyme.reports.api.dashboard_api.get_owner_dashboard_summary \
        -H 'Content-Type: application/json' \
        -d '{}')
    if echo "$dashboard_response" | grep -q "items"; then
        log_success "Owner dashboard: PASS"
    else
        log_error "Owner dashboard: FAIL"
        failed=1
    fi
    
    # Test 7: Check container health
    log "Test 7: Container health..."
    local unhealthy=$(docker ps --filter "health=unhealthy" -q | wc -l)
    if [ "$unhealthy" -eq 0 ]; then
        log_success "Container health: PASS (no unhealthy containers)"
    else
        log_error "Container health: FAIL ($unhealthy unhealthy containers)"
        failed=1
    fi
    
    # Test 8: Check for restart loops
    log "Test 8: Check for restart loops..."
    local restarting=$(docker ps --filter "status=restarting" -q | wc -l)
    if [ "$restarting" -eq 0 ]; then
        log_success "Restart loops: PASS (no restarting containers)"
    else
        log_error "Restart loops: FAIL ($restarting containers restarting)"
        failed=1
    fi
    
    # Cleanup
    rm -f /tmp/smoke_cookies.txt
    
    if [ $failed -eq 0 ]; then
        log_success "All smoke tests passed"
        return 0
    else
        log_error "Some smoke tests failed"
        return 1
    fi
}

# ============================================================
# POST-DEPLOY CLEANUP
# ============================================================

post_deploy_cleanup() {
    log "========== POST-DEPLOY CLEANUP =========="
    
    # Clean up build cache that was created during build
    docker builder prune -f 2>&1 | tee -a "$LOG_FILE"
    
    # Clean up dangling images
    docker image prune -f 2>&1 | tee -a "$LOG_FILE"
    
    local available_disk=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
    log_success "Post-deploy cleanup complete: ${available_disk}GB available"
}

# ============================================================
# MAIN DEPLOYMENT FLOW
# ============================================================

main() {
    log "=================================================="
    log "ScanifyMe Deployment Started"
    log "Timestamp: $(date)"
    log "Log file: $LOG_FILE"
    log "=================================================="
    
    # Step 1: Preflight checks
    if ! preflight_checks; then
        log_error "Preflight checks failed. Aborting deployment."
        exit 1
    fi
    
    # Step 2: Cleanup Docker (low-resource safety)
    cleanup_docker
    
    # Step 3: Build image
    if ! build_image; then
        log_error "Image build failed. Current system remains running."
        exit 1
    fi
    
    # Step 4: Restart services
    if ! restart_services; then
        log_error "Service restart failed. Manual intervention may be required."
        exit 1
    fi
    
    # Step 5: Run migrations
    if ! run_migrations; then
        log_error "Migration failed. Manual intervention may be required."
        exit 1
    fi
    
    # Step 6: Build assets
    build_assets
    
    # Step 7: Sync assets to frontend
    sync_assets
    
    # Step 8: Clear caches
    clear_caches
    
    # Step 9: Run smoke tests
    if ! smoke_tests; then
        log_error "Smoke tests failed. Deployment may have issues."
        log "Check logs: $LOG_FILE"
        log "See ROLLBACK section in SYSTEM_STATE.md for recovery steps"
        exit 1
    fi
    
    # Step 10: Post-deploy cleanup
    post_deploy_cleanup
    
    log "=================================================="
    log_success "Deployment completed successfully!"
    log "Log file: $LOG_FILE"
    log "=================================================="
    
    return 0
}

# Run main function
main "$@"
