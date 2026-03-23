# ScanifyMe Restore Guide

## Overview

This guide covers disaster recovery and restore procedures for the ScanifyMe production deployment.

## Prerequisites

- SSH access to VPS (root@91.107.206.65)
- Backup files available in `/opt/scanifyme/backups/`
- Docker and Docker Compose installed

## Quick Reference

### Emergency Rollback (Broken Deploy)

```bash
# 1. SSH to VPS
ssh root@91.107.206.65

# 2. Restore apps.json
cd /opt/scanifyme
cp apps.json.backup.* apps.json

# 3. Redeploy
./deploy/deploy.sh
```

### Full Restore from Backup

```bash
# 1. SSH to VPS
ssh root@91.107.206.65

# 2. List available backups
./deploy/backup.sh list

# 3. Extract backup
cd /opt/scanifyme/backups
tar -xzf scanifyme_backup_YYYYMMDD_HHMMSS.tar.gz

# 4. Restore database
docker exec -i scanifyme-db-1 mariadb -u root -pScanifyMe2026SecureDB scanifyme < scanifyme_backup_YYYYMMDD_HHMMSS/database.sql

# 5. Restore site config (if needed)
docker cp scanifyme_backup_YYYYMMDD_HHMMSS/site_config.json scanifyme-backend-1:/home/frappe/frappe-bench/sites/scanifyme.app/site_config.json

# 6. Restart services
docker compose --env-file .env -f compose.prod.yaml restart
```

## Restore Scenarios

### Scenario 1: Broken Deployment

**Symptoms:**
- Containers not starting
- API returning 500 errors
- Frontend not loading

**Steps:**

1. Check container status:
   ```bash
   docker ps -a | grep scanifyme
   ```

2. Check logs for errors:
   ```bash
   docker logs scanifyme-backend-1 --tail 100
   ```

3. Restore apps.json backup:
   ```bash
   cd /opt/scanifyme
   ls -la apps.json.*
   cp apps.json.backup.TIMESTAMP apps.json
   ```

4. Redeploy:
   ```bash
   ./deploy/deploy.sh
   ```

5. Validate:
   ```bash
   curl http://localhost:8080/api/method/ping
   curl http://localhost:8080/frontend
   ```

### Scenario 2: Migration Failure

**Symptoms:**
- Migration errors in logs
- Database schema mismatch
- App not loading after update

**Steps:**

1. Check migration status:
   ```bash
   docker exec scanifyme-backend-1 bench --site scanifyme.app migrate --list
   ```

2. If migration partially applied, check database:
   ```bash
   docker exec scanifyme-db-1 mariadb -u root -pScanifyMe2026SecureDB scanifyme -e "SHOW TABLES;"
   ```

3. Restore from backup:
   ```bash
   cd /opt/scanifyme/backups
   tar -xzf scanifyme_backup_YYYYMMDD_HHMMSS.tar.gz
   docker exec -i scanifyme-db-1 mariadb -u root -pScanifyMe2026SecureDB scanifyme < scanifyme_backup_YYYYMMDD_HHMMSS/database.sql
   ```

4. Restart and migrate:
   ```bash
   docker compose --env-file .env -f compose.prod.yaml restart backend
   docker exec scanifyme-backend-1 bench --site scanifyme.app migrate
   ```

### Scenario 3: Database Corruption

**Symptoms:**
- MariaDB not starting
- Table corruption errors
- Data inconsistencies

**Steps:**

1. Check database container:
   ```bash
   docker logs scanifyme-db-1 --tail 100
   ```

2. Try repair:
   ```bash
   docker exec scanifyme-db-1 mariadb-check -u root -pScanifyMe2026SecureDB --auto-repair scanifyme
   ```

3. If repair fails, restore from backup:
   ```bash
   # Stop all services except database
   docker compose --env-file .env -f compose.prod.yaml stop backend frontend websocket queue-short queue-long scheduler
   
   # Restore database
   cd /opt/scanifyme/backups
   tar -xzf scanifyme_backup_YYYYMMDD_HHMMSS.tar.gz
   docker exec -i scanifyme-db-1 mariadb -u root -pScanifyMe2026SecureDB scanifyme < scanifyme_backup_YYYYMMDD_HHMMSS/database.sql
   
   # Restart all services
   docker compose --env-file .env -f compose.prod.yaml up -d
   ```

### Scenario 4: Lost Site Config

**Symptoms:**
- Site configuration errors
- Authentication failures
- Database connection issues

**Steps:**

1. Check if config exists:
   ```bash
   docker exec scanifyme-backend-1 ls -la /home/frappe/frappe-bench/sites/scanifyme.app/site_config.json
   ```

2. Restore from backup:
   ```bash
   cd /opt/scanifyme/backups
   tar -xzf scanifyme_backup_YYYYMMDD_HHMMSS.tar.gz
   docker cp scanifyme_backup_YYYYMMDD_HHMMSS/site_config.json scanifyme-backend-1:/home/frappe/frappe-bench/sites/scanifyme.app/site_config.json
   ```

3. Restart backend:
   ```bash
   docker compose --env-file .env -f compose.prod.yaml restart backend
   ```

### Scenario 5: Missing Assets/Static Files

**Symptoms:**
- CSS/JS files returning 404
- Frontend styling broken
- Desk interface not loading

**Steps:**

1. Rebuild assets:
   ```bash
   docker exec scanifyme-backend-1 bench --site scanifyme.app build
   ```

2. Sync to frontend:
   ```bash
   docker cp scanifyme-backend-1:/home/frappe/frappe-bench/sites/assets/frappe/dist/css/. /tmp/css_backend/
   docker cp /tmp/css_backend/. scanifyme-frontend-1:/home/frappe/frappe-bench/sites/assets/frappe/dist/css/
   
   docker cp scanifyme-backend-1:/home/frappe/frappe-bench/sites/assets/frappe/dist/js/. /tmp/js_backend/
   docker cp /tmp/js_backend/. scanifyme-frontend-1:/home/frappe/frappe-bench/sites/assets/frappe/dist/js/
   ```

3. Clear cache:
   ```bash
   docker exec scanifyme-backend-1 bench --site scanifyme.app clear-cache
   ```

### Scenario 6: Container/Image Issues

**Symptoms:**
- Containers crashing
- Image pull failures
- Out of disk space

**Steps:**

1. Check disk space:
   ```bash
   df -h /
   docker system df
   ```

2. Clean up if needed:
   ```bash
   ./deploy/cleanup.sh safe
   ```

3. Rebuild image:
   ```bash
   cd /opt/scanifyme
   docker build \
     --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
     --build-arg=FRAPPE_BRANCH=version-16 \
     --build-arg=APPS_JSON_BASE64=$(base64 -w 0 apps.json) \
     --tag=scanifyme:v16 \
     --file=images/custom/Containerfile . \
     --load
   ```

4. Restart services:
   ```bash
   docker compose --env-file .env -f compose.prod.yaml up -d
   ```

## Restore Checklist

Before starting restore:
- [ ] Identify the failure scenario
- [ ] Verify backup availability
- [ ] Check disk space (need at least 5GB free)
- [ ] Document current state (logs, container status)
- [ ] Notify users if applicable

During restore:
- [ ] Stop affected services
- [ ] Restore in correct order (database first, then config)
- [ ] Verify each step before proceeding
- [ ] Keep backup of current state before overwriting

After restore:
- [ ] Verify all containers running
- [ ] Test API endpoints
- [ ] Test frontend loading
- [ ] Check logs for errors
- [ ] Run healthcheck
- [ ] Document what was restored

## Backup Contents

Each backup contains:
- `database.sql` - MariaDB database dump
- `site_config.json` - Site configuration
- `env.backup` - Environment variables
- `apps.json` - App configuration
- `manifest.txt` - Backup metadata

## Restore Order

1. **Database** - Always restore first
2. **Site Config** - If corrupted or missing
3. **Environment** - Only if .env was lost
4. **apps.json** - Only if changed incorrectly
5. **Services** - Restart after restore

## Verification Commands

After any restore, run these checks:

```bash
# Container status
docker ps | grep scanifyme

# API health
curl http://localhost:8080/api/method/ping

# Frontend
curl http://localhost:8080/frontend

# Database
docker exec scanifyme-db-1 mariadb-admin ping -u root -pScanifyMe2026SecureDB --silent

# Full healthcheck
./deploy/healthcheck.sh
```

## When to Rollback vs Restore

**Rollback** (use when):
- Last deployment failed
- apps.json was changed incorrectly
- Docker image build failed
- Quick fix needed

**Full Restore** (use when):
- Database corruption
- Data loss occurred
- Multiple components broken
- Rollback didn't work

## Contact and Support

For issues beyond this guide:
1. Check SYSTEM_STATE.md for known issues
2. Review deployment logs in /tmp/scanifyme-deploy-*.log
3. Run diagnostics: `./deploy/diagnostics.sh`
