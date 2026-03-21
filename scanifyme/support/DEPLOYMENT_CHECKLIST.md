# ScanifyMe Production Deployment Checklist

This checklist ensures ScanifyMe is ready for production deployment.

---

## 1. Pre-Deployment Validation

### 1.1 Database Migrations
```bash
# Verify all migrations are applied
bench --site {site_name} migrate

# Check for pending migrations
bench --site {site_name} list-migrations
```

- [ ] All migrations applied successfully
- [ ] No schema drift between code and database
- [ ] Fixtures loaded (roles, etc.)

### 1.2 Demo Data Separation
- [ ] Demo data NOT deployed to production
- [ ] Production users created
- [ ] Test tokens invalidated

### 1.3 Environment Variables
- [ ] `VITE_FRAPPE_URL` set correctly
- [ ] `VITE_USE_REALTIME` configured (default: false)
- [ ] `VITE_SOCKET_PORT` configured if realtime enabled
- [ ] No hardcoded local URLs

---

## 2. Infrastructure Dependencies

### 2.1 Redis
```bash
# Check Redis cache connectivity
redis-cli -h {redis_host} -p 13000 ping
# Expected: PONG

# Check Redis queue connectivity  
redis-cli -h {redis_host} -p 13002 ping
# Expected: PONG
```

- [ ] Redis cache (port 13000) accessible
- [ ] Redis queue (port 13002) accessible
- [ ] Redis configuration matches site_config.json

### 2.2 Database
- [ ] Database backup taken before deployment
- [ ] Connection credentials verified
- [ ] Database type (MariaDB/MySQL) matches configuration

### 2.3 Scheduler & Workers
```bash
# Verify scheduler is enabled
bench --site {site_name} enable-scheduler

# Check worker status
bench --site {site_name} show-pending-jobs
```

- [ ] Scheduler enabled
- [ ] Worker process running (`bench start`)
- [ ] Background jobs processing

### 2.4 Web Server
```bash
# Test web server response
curl -I http://{site_url}/api/method/ping
# Expected: HTTP 200
```

- [ ] Web server responding on port 8000/443
- [ ] SSL/TLS configured (HTTPS)
- [ ] Site accessible

---

## 3. Email Configuration

### 3.1 Email Account Setup
```bash
# Via console
bench --site {site_name} console
>>> frappe.get_all('Email Account', fields=['name', 'email_id', 'enable_outgoing', 'default_outgoing'])
```

- [ ] Email Account created
- [ ] Outgoing email enabled
- [ ] Default outgoing set
- [ ] SMTP credentials configured

### 3.2 Email Queue Testing
```bash
# Via console - test email send
>>> frappe.sendmail(recipients=['test@example.com'], subject='Test', message='<p>Test</p>')
>>> frappe.db.commit()
>>> frappe.get_all('Email Queue', fields=['name', 'status'])
```

- [ ] Email queue entry created
- [ ] Email sent successfully (or in queue)
- [ ] No SMTP errors in logs

---

## 4. ScanifyMe-Specific Checks

### 4.1 App Installation
```bash
# Verify ScanifyMe is installed
bench --site {site_name} list-apps
# Should show: scanifyme
```

- [ ] ScanifyMe app installed on site
- [ ] All DocTypes loaded
- [ ] Module structure correct

### 4.2 QR System Validation
```bash
# Create test QR batch
bench --site {site_name} execute scanifyme.qr_management.services.qr_service.create_qr_batch --args "{'batch_name': 'Test', 'batch_size': 5}"

# Verify batch created
bench --site {site_name} console
>>> frappe.get_all('QR Batch', fields=['name', 'status'], limit=5)
```

- [ ] QR Batch creation works
- [ ] QR Code Tags generated
- [ ] Token generation functional

### 4.3 API Accessibility
```bash
# Test public scan API (no auth)
curl -X POST http://{site_url}/api/method/scanifyme.public_portal.api.public_api.get_public_item_context \
  -H "Content-Type: application/json" \
  -d '{"token": "INVALID"}'
# Expected: {"success": false, "error": "..."}

# Test authenticated API (as admin)
curl -X POST http://{site_url}/api/method/frappe.auth.get_logged_user
# Expected: {"message": "Administrator"}
```

- [ ] Public APIs accessible (no auth leakage)
- [ ] Auth check working
- [ ] No traceback in error responses

---

## 5. RBAC & Permissions

### 5.1 Role Verification
```bash
bench --site {site_name} console
>>> frappe.get_roles('Administrator')
>>> frappe.get_roles('ScanifyMe Admin')
>>> frappe.get_roles('ScanifyMe Operations')
>>> frappe.get_roles('ScanifyMe Support')
```

- [ ] Administrator has full access
- [ ] ScanifyMe Admin role exists
- [ ] ScanifyMe Operations role exists
- [ ] ScanifyMe Support role exists

### 5.2 Permission Tests
- [ ] Admin can access all DocTypes
- [ ] Admin can access operational APIs
- [ ] Owners can only access own data
- [ ] Guests can only access public APIs
- [ ] No permission escalation vulnerabilities

---

## 6. Smoke Test Commands

### 6.1 Environment Health
```bash
bench --site {site_name} execute scanifyme.support.api.support_api.get_environment_health_summary
```
**Expected**: JSON with `overall_status`, `checks` array, `summary`
**Healthy**: `overall_status` = "healthy"

### 6.2 Operational Health
```bash
bench --site {site_name} execute scanifyme.support.api.support_api.get_operational_health_summary
```
**Expected**: JSON with notification backlog, recovery case stats

### 6.3 Setup Validation
```bash
bench --site {site_name} execute scanifyme.support.api.support_api.validate_scanifyme_setup
```
**Expected**: JSON with `setup_status` = "ready" or "warning"

### 6.4 Notification Queue Status
```bash
bench --site {site_name} execute scanifyme.support.api.support_api.get_notification_queue_status
```
**Expected**: JSON with queue counts (queued, sent, failed, skipped)

### 6.5 Stale Cases Report
```bash
bench --site {site_name} execute scanifyme.support.api.support_api.get_stale_cases_report
```
**Expected**: JSON with `stale_count` and `cases` array

### 6.6 Queue Failure Report
```bash
bench --site {site_name} execute scanifyme.support.api.support_api.get_queue_failure_report
```
**Expected**: JSON with failure summaries

---

## 7. Route Verification

### 7.1 Admin Routes (Desk)
```bash
# All should return HTTP 200
curl -I http://{site_url}/app
curl -I http://{site_url}/app/notification-event-log
curl -I http://{site_url}/app/recovery-case
curl -I http://{site_url}/app/email-queue
```

### 7.2 Frontend Routes (React SPA)
```bash
# All should return HTTP 200
curl -I http://{site_url}/frontend
curl -I http://{site_url}/frontend/items
curl -I http://{site_url}/frontend/recovery
curl -I http://{site_url}/frontend/notifications
curl -I http://{site_url}/frontend/settings
```

### 7.3 Public Routes
```bash
# Should return HTTP 200 with safe error for invalid token
curl -I http://{site_url}/s/INVALID_TOKEN
```

---

## 8. Frontend Build Verification

```bash
cd apps/scanifyme/frontend
yarn build
```

- [ ] Build completes without errors
- [ ] Assets generated in `dist/` or `build/`
- [ ] No `/frontend/api/` URL patterns in built code
- [ ] No `Invalid URL` patterns
- [ ] API base URL correctly embedded

---

## 9. Operational Visibility

### 9.1 Admin Desk Views
- [ ] Notification Event Log list loads
- [ ] Recovery Case list loads
- [ ] Finder Session list loads
- [ ] Email Queue list loads
- [ ] Error Log accessible

### 9.2 Operational APIs
```bash
# Test diagnostic bundle
bench --site {site_name} execute scanifyme.support.api.support_api.get_case_diagnostic_bundle --args "'CASE_NAME'"
```

- [ ] Returns comprehensive case data
- [ ] Includes timeline, messages, notifications, emails

### 9.3 Maintenance Actions
```bash
# List available actions
bench --site {site_name} execute scanifyme.support.api.support_api.get_maintenance_actions
```

- [ ] Returns action list
- [ ] Actions are clearly documented

---

## 10. Backup & Rollback

### 10.1 Pre-Deployment Backup
```bash
# Database backup
bench --site {site_name} backup --with-files

# App code backup
cp -r apps/scanifyme ~/backup_scanifyme_$(date +%Y%m%d)
```

- [ ] Database backup completed
- [ ] App code backed up
- [ ] Backup verified (can restore)

### 10.2 Rollback Plan
- [ ] Previous version tagged
- [ ] Rollback procedure documented
- [ ] Database rollback tested (non-production)

---

## 11. Monitoring Setup

### 11.1 Health Check Endpoint
```bash
# Lightweight health check
bench --site {site_name} execute scanifyme.support.api.support_api.get_quick_health_check
```
**Expected**: `{"status": "healthy"}`

### 11.2 Error Log Monitoring
- [ ] Error Log DocType accessible
- [ ] Alerts configured for critical errors
- [ ] Log rotation configured

---

## 12. Post-Deployment Verification

### 12.1 Smoke Test After Deploy
```bash
# Wait 30 seconds for services to stabilize

# 1. Health check
curl http://{site_url}/api/method/ping

# 2. Public scan
curl -X POST http://{site_url}/api/method/scanifyme.public_portal.api.public_api.get_public_item_context \
  -d '{"token": "INVALID"}'

# 3. Notification queue
bench --site {site_name} execute scanifyme.support.api.support_api.get_notification_queue_status
```

### 12.2 Key Workflow Test
1. Register a test item
2. Activate a QR code
3. Submit a test message
4. Verify notification created
5. Verify recovery case created

### 12.3 Performance Baseline
- [ ] Page load times recorded
- [ ] API response times recorded
- [ ] No memory leaks observed

---

## Quick Reference: Actor Logins

| Actor | Login | Password | Access |
|-------|-------|----------|--------|
| Admin | Administrator | admin | Full system |
| Owner A | owner_a@scanifyme.app | (configured) | Full onboarding |
| Owner B | owner_b_partial@scanifyme.app | (configured) | Partial |
| Demo | demo@scanifyme.app | (configured) | Primary demo |

---

## Quick Reference: Key Commands

```bash
# Migration
bench --site {site} migrate

# Demo data (development only!)
bench --site {site} execute scanifyme.api.demo_data.create_demo_data
bench --site {site} execute scanifyme.api.demo_data.get_operational_demo_summary

# Health check
bench --site {site} execute scanifyme.support.api.support_api.get_environment_health_summary
bench --site {site} execute scanifyme.support.api.support_api.validate_scanifyme_setup

# Operational summary
bench --site {site} execute scanifyme.support.api.support_api.get_notification_queue_status
bench --site {site} execute scanifyme.support.api.support_api.get_queue_failure_report

# Maintenance
bench --site {site} execute scanifyme.support.api.support_api.get_maintenance_actions
bench --site {site} execute scanifyme.support.api.support_api.run_safe_maintenance_action --args "'recompute_all_case_metadata'"
```

---

**Deployment Date**: ________________
**Deployed By**: ________________
**Version**: ________________
**Notes**: ________________
