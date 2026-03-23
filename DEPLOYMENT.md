# ScanifyMe Deployment Documentation

## Deployment Summary

**Date**: 2026-03-21
**VPS**: 91.107.206.65
**Site**: scanifyme.app
**Frappe Version**: version-16
**Custom App**: scanifyme (from GitHub main)

## Deployment Architecture

### Components
- **frappe_docker**: `main` branch from https://github.com/frappe/frappe_docker
- **Custom Image**: `scanifyme:v16` (built with frappe v16 + scanifyme app)
- **Database**: MariaDB (via `compose.mariadb.yaml`)
- **Cache**: Redis (via `compose.redis.yaml`)
- **Ports**: 8080 (HTTP)

### Container List
| Container | Status | Purpose |
|-----------|--------|---------|
| scanifyme-db-1 | Healthy | MariaDB database |
| scanifyme-redis-cache-1 | Running | Redis cache |
| scanifyme-redis-queue-1 | Running | Redis queue |
| scanifyme-backend-1 | Running | Frappe backend |
| scanifyme-frontend-1 | Running | Nginx reverse proxy |
| scanifyme-websocket-1 | Running | Socket.IO |
| scanifyme-queue-short-1 | Running | Short job queue |
| scanifyme-queue-long-1 | Running | Long job queue |
| scanifyme-scheduler-1 | Running | Scheduled tasks |

## Deployment Directory Structure

```
/opt/scanifyme/
├── apps.json           # Custom app definition (scanifyme)
├── .env               # Environment variables
├── compose.yaml        # Base compose file
├── compose.prod.yaml  # Production compose (merged)
├── images/            # Docker image definitions
└── overrides/         # Compose overrides
```

## Key Files

### apps.json
```json
[
  {
    "url": "https://github.com/vineelreddy10/scanifyme.git",
    "branch": "main"
  }
]
```

### .env (excerpt)
```
FRAPPE_VERSION=version-16
ERPNEXT_VERSION=v16.10.1
DB_PASSWORD=ScanifyMe2026SecureDB
REDIS_CACHE=redis-cache:6379
REDIS_QUEUE=redis-queue:6379
SITES=scanifyme.app
SITE_NAME=scanifyme.app
CUSTOM_IMAGE=scanifyme
CUSTOM_TAG=v16
PULL_POLICY=missing
ADMIN_PASSWORD=admin@123
HTTP_PUBLISH_PORT=8080
```

## How to Redeploy ScanifyMe from GitHub main

### SSH into VPS
```bash
ssh root@91.107.206.65
cd /opt/scanifyme
```

### Pull Latest App Code
Since the app is built into the image, you need to rebuild:
```bash
# Update apps.json if needed (already points to main)
# Rebuild custom image
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --build-arg=APPS_JSON_BASE64=$(base64 -w 0 apps.json) \
  --tag=scanifyme:v16 \
  --file=images/custom/Containerfile . \
  --load

# Restart containers
docker compose --env-file .env -f compose.prod.yaml up -d
```

### Run Migrations
```bash
docker exec scanifyme-backend-1 bench --site scanifyme.app migrate
```

## How to Restart Containers

```bash
cd /opt/scanifyme
docker compose --env-file .env -f compose.prod.yaml restart
```

## How to Stop Containers

```bash
cd /opt/scanifyme
docker compose --env-file .env -f compose.prod.yaml down
```

## How to Inspect Logs

```bash
# All containers
docker compose --env-file .env -f compose.prod.yaml logs -f

# Specific container
docker compose --env-file .env -f compose.prod.yaml logs -f backend

# Last 100 lines
docker compose --env-file .env -f compose.prod.yaml logs --tail=100
```

## How to Re-run Migrations

```bash
docker exec scanifyme-backend-1 bench --site scanifyme.app migrate
```

## How to Recreate Site (Fresh Start)

```bash
# Connect to backend
docker exec -it scanifyme-backend-1 bash

# Drop existing site
rm -rf /home/frappe/frappe-bench/sites/scanifyme.app

# Recreate site
bench new-site scanifyme.app --mariadb-root-password ScanifyMe2026SecureDB --admin-password admin@123

# Install app
bench --site scanifyme.app install-app scanifyme

# Migrate
bench --site scanifyme.app migrate
```

## Rollback / Recovery Notes

### If deployment fails:
1. Check container logs: `docker compose logs`
2. Check database: `docker exec scanifyme-db-1 mariadb -u root -p...`
3. Verify environment: `docker exec scanifyme-backend-1 env | grep -E 'DB|REDIS|SITE'`

### If site is broken:
1. Backup database volume first
2. Drop site and recreate (see above)

### If image fails to build:
1. Check disk space: `df -h /`
2. Clear Docker cache: `docker system prune -a`
3. Retry build with `--no-cache`

## Validation Commands

```bash
# Test /app
curl -sL -o /dev/null -w "%{http_code}" http://91.107.206.65:8080/app

# Test /frontend
curl -sL -o /dev/null -w "%{http_code}" http://91.107.206.65:8080/frontend

# Test API
curl -sL http://91.107.206.65:8080/api/method/ping

# List installed apps
docker exec scanifyme-backend-1 bench --site scanifyme.app list-apps
```

## Secrets and Credentials

| Item | Value | Location |
|------|-------|----------|
| MariaDB Password | ScanifyMe2026SecureDB | /opt/scanifyme/.env |
| Admin Password | admin@123 | Site config |
| Site Name | scanifyme.app | /opt/scanifyme/.env |

**IMPORTANT**: Backup `/opt/scanifyme/.env` - it contains credentials.

## Known Constraints

1. **No HTTPS**: Currently using HTTP on port 8080. Configure Traefik or nginx-proxy for HTTPS.
2. **No Email**: Email not configured. Configure Email Account via Desk.
3. **No Backup**: No automated backups configured. Set up backup strategy.

## Emergency Contacts

- **VPS SSH**: `ssh root@91.107.206.65`
- **Docker Directory**: `/opt/scanifyme`
