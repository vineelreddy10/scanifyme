# ScanifyMe Deployment Automation

## Overview

This directory contains deployment automation scripts for the ScanifyMe platform, designed for safe, repeatable deployments to a low-resource VPS (2 vCPU, 4GB RAM, 40GB disk).

## Files

- **`deploy.sh`** - Main deployment script with preflight checks, build, migration, and smoke tests
- **`rollback.sh`** - Rollback helper for diagnosing and recovering from failed deployments

## Quick Start

### Automated Deployment (GitHub Actions)

Push to `main` branch to trigger automatic deployment:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

### Manual Deployment (SSH)

SSH into the VPS and run:

```bash
ssh root@91.107.206.65
cd /opt/scanifyme
/path/to/deploy.sh
```

Or from local machine:

```bash
ssh root@91.107.206.65 "cd /opt/scanifyme && bash -s" < deploy/deploy.sh
```

### Rollback / Diagnostics

```bash
ssh root@91.107.206.65
cd /opt/scanifyme
/path/to/rollback.sh diagnose
/path/to/rollback.sh status
/path/to/rollback.sh restart
/path/to/rollback.sh logs
```

## Deployment Flow

### Preflight Checks
1. Verify deployment directory exists
2. Check Docker and Docker Compose available
3. Verify required files (compose.yaml, .env, apps.json)
4. Check minimum disk space (10GB)
5. Verify Docker daemon is running

### Build & Deploy
1. Clean Docker resources (low-resource safety)
2. Build Docker image with latest code
3. Restart services
4. Run database migrations
5. Build frontend assets
6. Sync assets to frontend container
7. Clear application caches

### Post-Deploy Validation
1. API ping test
2. Frontend load test
3. Login authentication test
4. QR Batch list API test
5. Filtered QR Code Tag list test
6. Owner dashboard API test
7. Container health check
8. Restart loop detection

## GitHub Actions Secrets Required

Configure these secrets in your GitHub repository:

| Secret | Description | Example |
|--------|-------------|---------|
| `VPS_HOST` | VPS IP address | `91.107.206.65` |
| `VPS_USER` | SSH username | `root` |
| `VPS_SSH_KEY` | SSH private key | (your private key) |

## Low-Resource VPS Safety

The deployment automation includes specific safety measures for the constrained VPS:

- **Disk space check**: Minimum 10GB free before deployment
- **Docker cleanup**: Removes dangling images, build cache, stopped containers
- **Volume protection**: Never removes volumes (would delete database)
- **Build cache cleanup**: Clears build cache after deployment
- **Memory monitoring**: Checks for OOM kills and restart loops

## Smoke Tests

After deployment, the following tests run automatically:

1. **API Ping** - Verifies API is responding
2. **Frontend Load** - Checks React SPA loads
3. **Login** - Tests authentication flow
4. **QR Batch List** - Tests list API
5. **Filtered QR List** - Tests filter contract (dict format)
6. **Owner Dashboard** - Tests owner API
7. **Container Health** - Checks for unhealthy containers
8. **Restart Loops** - Detects container restart issues

## Rollback Procedures

### If Deployment Fails

1. **Check logs**:
   ```bash
   ssh root@91.107.206.65
   cd /opt/scanifyme
   ./deploy/rollback.sh logs
   ```

2. **Run diagnostics**:
   ```bash
   ./deploy/rollback.sh diagnose
   ```

3. **Restart services** (if containers are in bad state):
   ```bash
   ./deploy/rollback.sh restart
   ```

### If Migration Fails

1. Check migration logs:
   ```bash
   docker logs scanifyme-backend-1 --tail 100
   ```

2. The system will remain on the previous version if migration fails
3. Manual intervention may be required

### If Build Fails

The current running system remains intact if build fails. No rollback needed.

## Known Constraints

- **Build time**: 5-10 minutes (limited CPU)
- **Disk space**: Build cache can consume ~19GB
- **Memory**: 4GB RAM limits concurrent operations
- **No swap**: Memory pressure can cause OOM kills

## Troubleshooting

### Deployment stuck
```bash
# Check container status
docker ps

# Check for resource issues
docker stats --no-stream

# Force restart
cd /opt/scanifyme
docker compose --env-file .env -f compose.prod.yaml down
docker compose --env-file .env -f compose.prod.yaml up -d
```

### API not responding
```bash
# Check backend logs
docker logs scanifyme-backend-1 --tail 50

# Check if backend is running
docker ps | grep backend

# Restart backend
docker restart scanifyme-backend-1
```

### Frontend not loading
```bash
# Check frontend logs
docker logs scanifyme-frontend-1 --tail 50

# Check if assets exist
docker exec scanifyme-frontend-1 ls /home/frappe/frappe-bench/sites/assets/frappe/dist/css/

# Sync assets manually
docker cp scanifyme-backend-1:/home/frappe/frappe-bench/sites/assets/frappe/dist/css/. /tmp/css_backend/
docker cp /tmp/css_backend/. scanifyme-frontend-1:/home/frappe/frappe-bench/sites/assets/frappe/dist/css/
```

## Support

For deployment issues, check:
1. This README
2. `SYSTEM_STATE.md` in the app directory
3. Container logs
4. GitHub Actions workflow runs
