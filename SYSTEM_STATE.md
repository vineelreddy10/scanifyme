# ScanifyMe - System Architecture State

## Overview
ScanifyMe is a QR-based item recovery platform built on Frappe (Python) backend with React (TypeScript) frontend.

---

## Modules

### Backend Modules (Frappe)

| Module | Purpose |
|--------|---------|
| `scanifyme_core` | Core functionality, settings, shared utilities |
| `qr_management` | QR code generation and management |
| `ownership` | Ownership tracking and transfers |
| `items` | Item management |
| `recovery` | Recovery process management |
| `messaging` | Messaging system between finders and owners |
| `notifications` | Notification system |
| `public_portal` | Public facing pages (guest access) |
| `admin_ops` | Admin operations |
| `reports` | Reporting and analytics |

---

## Roles

| Role | Description |
|------|-------------|
| `ScanifyMe User` | Standard user - can manage own items and QR codes |
| `ScanifyMe Operations` | Operations manager - manages QR inventory and recoveries |
| `ScanifyMe Support` | Support agent - handles recovery support |
| `ScanifyMe Admin` | System administrator - full system access |

---

## DocTypes

### Created
- **ScanifyMe Settings** (Singleton)
  - `site_name`: Data
  - `default_privacy_level`: Select (High/Medium/Low)
  - `allow_anonymous_messages`: Check
  - `allow_location_sharing`: Check
  - `default_reward_message`: Text Editor
  - `max_messages_per_hour`: Int
  - `max_scans_per_minute`: Int

- **QR Batch**
  - `naming_series`: Select
  - `batch_name`: Data
  - `batch_prefix`: Data
  - `batch_size`: Int
  - `status`: Select (Draft, Generated, Printed, Distributed, Closed)
  - `created_by`: Link User
  - `created_on`: Datetime

- **QR Code Tag**
  - `qr_uid`: Data (unique)
  - `qr_token`: Data (unique)
  - `qr_url`: Data
  - `batch`: Link QR Batch
  - `status`: Select (Generated, Printed, In Stock, Assigned, Activated, Suspended, Retired)
  - `registered_item`: Link Registered Item (future)
  - `created_on`: Datetime

- **Owner Profile**
  - `user`: Link User (unique)
  - `display_name`: Data
  - `phone`: Data
  - `address`: Text
  - `default_recovery_note`: Text
  - `is_verified`: Check
  - `total_items`: Int (read only)
  - `active_items`: Int (read only)
  - `recovered_items`: Int (read only)
  - `created_on`: Datetime
  - `modified_on`: Datetime

- **Item Category**
  - `category_name`: Data (unique)
  - `category_code`: Data (unique)
  - `description`: Text
  - `icon`: Data
  - `is_active`: Check
  - `item_count`: Int (read only)
  - `parent_category`: Link Item Category

- **Registered Item**
  - `item_name`: Data
  - `owner_profile`: Link Owner Profile
  - `qr_code_tag`: Link QR Code Tag
  - `item_category`: Link Item Category
  - `public_label`: Data
  - `recovery_note`: Text
  - `reward_note`: Text
  - `status`: Select (Draft, Active, Lost, Recovered, Archived)
  - `activation_date`: Datetime (read only)
  - `last_scan_at`: Datetime (read only)
  - `photos`: Table (Item Photo)

- **Item Photo** (Child Table)
  - `image`: Attach Image
  - `visibility`: Select (Private, Public)
  - `caption`: Data

- **Ownership Transfer**
  - `item`: Link Registered Item
  - `from_owner`: Link Owner Profile
  - `to_owner`: Link Owner Profile
  - `status`: Select (Pending, Approved, Rejected, Completed)
  - `transfer_token`: Data (unique, read only)
  - `created_on`: Datetime
  - `completed_on`: Datetime
  - `notes`: Text

- **Recovery Case** (NEW)
  - `case_title`: Data
  - `qr_code_tag`: Link QR Code Tag
  - `registered_item`: Link Registered Item
  - `owner_profile`: Link Owner Profile
  - `status`: Select (Open, Owner Responded, Return Planned, Recovered, Closed, Invalid, Spam)
  - `opened_on`: Datetime
  - `last_activity_on`: Datetime
  - `closed_on`: Datetime
  - `finder_session_id`: Data
  - `latest_message_preview`: Data
  - `finder_name`: Data
  - `finder_contact_hint`: Data
  - `notes_internal`: Small Text

- **Recovery Message** (NEW)
  - `recovery_case`: Link Recovery Case
  - `sender_type`: Select (Finder, Owner, System)
  - `sender_name`: Data
  - `message`: Text
  - `attachment`: Attach
  - `created_on`: Datetime
  - `is_public_submission`: Check
  - `is_read_by_owner`: Check

- **Scan Event** (NEW)
  - `qr_code_tag`: Link QR Code Tag
  - `registered_item`: Link Registered Item
  - `token`: Data
  - `scanned_on`: Datetime
  - `ip_hash`: Data
  - `user_agent`: Small Text
  - `route`: Data
  - `status`: Select (Valid, Invalid, Unavailable, Recovery Initiated)
  - `recovery_case`: Link Recovery Case

- **Finder Session** (NEW)
  - `session_id`: Data (unique)
  - `qr_code_tag`: Link QR Code Tag
  - `started_on`: Datetime
  - `last_seen_on`: Datetime
  - `ip_hash`: Data
  - `user_agent`: Small Text
  - `status`: Select (Active, Closed, Expired, Blocked)

---

## APIs

### Whitelisted Methods

| Method | Module | Access | Purpose |
|--------|--------|--------|---------|
| `get_settings` | scanifyme_core | Authenticated | Get singleton settings |
| `get_public_settings` | scanifyme_core | Guest | Get public settings |
| `update_settings` | scanifyme_core | Admin | Update settings |
| `get_user_role` | api | Authenticated | Get current user's role |
| `create_qr_batch` | qr_management.api | Admin/Operations | Create QR batch |
| `get_qr_batches` | qr_management.api | Admin/Operations | List QR batches |
| `get_qr_tags` | qr_management.api | Admin/Operations | List QR tags |
| `get_qr_preview` | qr_management.api | Admin/Operations | Preview QR by token |
| `activate_qr` | items.api | Authenticated | Activate QR code for item registration |
| `create_item` | items.api | Authenticated | Create a new registered item |
| `get_user_items` | items.api | Authenticated | Get items for current user |
| `get_item_details` | items.api | Authenticated | Get detailed item information |
| `update_item_status` | items.api | Authenticated | Update item status |
| `link_item_to_qr` | items.api | Authenticated | Link item to QR code tag |
| `get_item_categories` | items.api | Authenticated | Get all active item categories |

### QR Services

| Function | Module | Purpose |
|----------|--------|---------|
| `generate_qr_token()` | qr_management.services.qr_service | Generate random 8-12 char token |
| `generate_qr_uid()` | qr_management.services.qr_service | Generate human-readable UID |
| `generate_qr_url()` | qr_management.services.qr_service | Generate public URL /s/token |
| `generate_qr_image()` | qr_management.services.qr_service | Generate QR image using File API |
| `generate_qr_batch()` | qr_management.services.qr_service | Create batch of QR codes |
| `get_public_qr()` | qr_management.services.qr_service | Get public QR by token |

### Item Services

| Function | Module | Purpose |
|----------|--------|---------|
| `activate_qr()` | items.services.item_service | Activate QR code for item |
| `create_item()` | items.services.item_service | Create registered item |
| `link_item_to_qr()` | items.services.item_service | Link item to QR tag |
| `get_user_items()` | items.services.item_service | Get items for user |
| `get_item_details()` | items.services.item_service | Get item details (sanitized) |
| `update_item_status()` | items.services.item_service | Update item status |
| `get_or_create_owner_profile()` | items.services.item_service | Get or create owner profile |

### Public Token Format
QR codes use secure tokens in URL: `/s/<secure_token>`
Example: `https://scanifyme.app/s/X7K9M4PQ`

---

## Routing Architecture

### SPA Mount Point
- React SPA mounted at `/frontend`
- BrowserRouter uses `basename="/frontend"`

### Route Structure (relative to /frontend)
| Path | Component | Purpose |
|------|-----------|---------|
| `/` | Dashboard | Main dashboard with QR stats |
| `/settings` | Settings | Settings management |
| `/items` | Items | User's registered items |
| `/items/:id` | ItemDetail | Item details and management |
| `/activate-qr` | ActivateQR | QR code activation and item creation |

### Full URLs
- Dashboard: `/frontend/`
- Settings: `/frontend/settings`
- Items: `/frontend/items`
- Item Detail: `/frontend/items/:id`
- Activate QR: `/frontend/activate-qr`

### Desk Integration (Admin)
- QR Batch: `/app/qr-batch`
- QR Code Tag: `/app/qr-code-tag`
- Settings: `/app/settings`

### Public Finder
- Scan URL: `/s/<token>`

---

## Frontend Routes

| Route | Auth | Purpose |
|-------|------|---------|
| `/` | Auth | Main dashboard with QR stats (maps to /frontend/) |
| `/settings` | Auth | Settings management |
| `/items` | Auth | User's registered items with table view |
| `/items/:id` | Auth | Item detail page with status management |
| `/activate-qr` | Auth | QR code activation with item creation form |

**Note**: Unauthenticated users are redirected to Frappe Desk login (`/login`)

---

## Frontend Structure

```
src/
├── api/
│   └── frappe.ts          # API wrapper (QR + Items functions)
├── contexts/
│   └── AuthContext.tsx   # Auth context provider
├── hooks/                 # Custom React hooks (future)
├── pages/
│   ├── Dashboard.tsx     # Dashboard page
│   ├── Settings.tsx      # Settings page
│   ├── Items.tsx         # User's items with table
│   ├── ItemDetail.tsx    # Item detail with status management
│   └── ActivateQR.tsx    # QR activation and item creation
├── components/           # Reusable components (future)
├── layouts/              # Layout components (future)
├── utils/                # Utility functions (future)
├── App.tsx               # Main app with routing
└── main.tsx              # Entry point
```

---

## Authentication

- Uses `frappe-react-sdk` with `useFrappeAuth` hook
- `FrappeProvider` wraps the app
- Custom `AuthProvider` provides authentication state
- **Uses Frappe Desk login** - unauthenticated users redirected to `/login`
- After login via Frappe Desk, users can access the app

---

## Security Rules

1. Guest must never access internal doctypes
2. Public APIs must use `allow_guest=True`
3. All public responses must sanitize owner information
4. Public URLs follow format: `/s/<secure_token>`
5. QR tokens must not expose DocType names or database IDs

---

## Desk Integration

- QR Batch list view available in Desk at `/app/qr-batch`
- QR Code Tag list view available in Desk at `/app/qr-code-tag`
- Workspace: "ScanifyMe Operations" added via config/desktop.py

---

## Next Steps (Future Prompts)

1. ~~Implement QR code generation and management~~ (COMPLETED)
2. ~~Implement QR Activation and Item Registration~~ (COMPLETED)
3. Build recovery workflow
4. Implement messaging between finder and owner
5. Add notification system
6. Create public scan page for guests

---

## Testing Infrastructure

### Backend Tests
- Location: `scanifyme/items/tests/test_item_service.py`
- Run with: `python -m pytest scanifyme/items/tests/`
- Tests: activate_qr, create_item, link_item_to_qr, get_user_items

### Frontend Tests (Playwright)
- Location: `frontend/tests/scanifyme.spec.ts`
- Config: `frontend/playwright.config.ts`
- Run with: `cd frontend && npx playwright test`
- Tests: SPA loading, route navigation, form submission

---

## Frontend API Architecture

### API Base Path
All API calls use base path: `/api`
- Method calls: `/api/method/<method-path>`
- Resource calls: `/api/resource/<doctype>`

### API Wrapper Configuration
- File: `frontend/src/api/frappe.ts`
- Uses environment variable: `VITE_FRAPPE_URL`
- Default: Empty string (same origin)

### Example API Calls
```
GET  /api/method/scanifyme.qr_management.api.qr_api.get_qr_batches
POST /api/method/scanifyme.items.api.items_api.get_user_items
```

### React Routes
All routes under `/frontend/*`:
- `/frontend` - Dashboard
- `/frontend/items` - User's items
- `/frontend/items/:id` - Item detail
- `/frontend/activate-qr` - QR activation

### Important Notes
- API calls NEVER prefixed with `/frontend`
- BrowserRouter basename is `/frontend`
- CSRF token handled via session cookies (`credentials: "include"`)

---

## CSRF Handling

### Configuration
- POST requests include: `credentials: "include"`
- Content-Type: `application/json`
- CSRF token read automatically from session cookie by Frappe backend
- No manual CSRF header required when using session cookies

### Security
- Session cookies contain `csrf_token`
- Frappe validates CSRF token on all POST requests
- Token rotation handled by Frappe session management

---

## Installation

After app installation:
```bash
bench install-app scanifyme
bench --site [site-name] migrate
```

Build frontend:
```bash
cd frontend && yarn install && yarn build
```

---

## Infrastructure Requirements

### Development Environment Dependencies

The Frappe development environment requires the following Redis services:

| Service | Port | Purpose |
|---------|------|---------|
| Redis Cache | 13002 | Session data, cache |
| Redis Queue | 11002 | Background job queue |
| Redis SocketIO | 13002 | Real-time updates |

### Starting the Development Environment

```bash
# Start Redis manually if bench fails to start them
redis-server --port 13002 --daemonize yes --dir /tmp --dbfilename dump13002.rdb
redis-server --port 11002 --daemonize yes --dir /tmp --dbfilename dump11002.rdb

# Then start bench
bench start
```

### Redis Failure Symptoms

If Redis is unavailable, Frappe will show:
- `redis.exceptions.ConnectionError: Error 111 connecting to 127.0.0.1:13002. Connection refused.`
- `frappe.exceptions.SessionBootFailed`
- Desk pages will not load
- Frontend API calls will fail

### Verification

Test Redis:
```bash
redis-cli -p 13002 ping  # Should return PONG
redis-cli -p 11002 ping  # Should return PONG
```

Test API:
```bash
curl -s http://127.0.0.1:8002/api/method/ping  # Should return 200
```

---

## Frontend Routing Rules

1. React SPA routes must always live under /frontend/*
2. BrowserRouter must use: `basename="/frontend"`
3. API routes must always use /api/*
4. Never prefix API calls with /frontend
5. Never use /dashboard - use "/" for frontend root
6. Admin UI belongs in /app/* using Frappe Desk

---

## Frontend API Rules

1. FrappeProvider url must be:
   - Empty string "" for same-origin requests (RECOMMENDED)
   - Full URL like "http://localhost:8000" for cross-origin
   - NEVER "/" (causes Invalid URL error in URL constructor)
2. API routes always under /api/*
3. Never prefix API calls with /frontend
4. Never depend on pathname for API base URL

---

## Debugging Lessons

### Invalid URL Error Resolution

**Root Cause**: The frappe-react-sdk internally uses `new URL(endpoint, baseUrl)`. When `VITE_FRAPPE_URL` was set to "/" in `.env.local`, it was passed to FrappeProvider as the base URL. The URL constructor fails with "/" because it's not a valid absolute URL.

**Fix Applied**:
- Changed FrappeProvider url from "/" to "" (empty string for same-origin)
- Changed API wrapper to use "" instead of "/" for same-origin
- Added explicit check to exclude "/" from being used as base URL

**Prevention Rules**:
1. Never pass "/" as the base URL to FrappeProvider - use "" instead
2. Use empty string for same-origin API calls (relative URLs)
3. Only use VITE_FRAPPE_URL if it's a valid absolute URL (e.g., "http://localhost:8000")
4. Test frontend routes after any configuration changes

### Static Validation Checklist

Run these checks after any frontend changes:
```bash
# Check for /dashboard references (should be 0)
grep -r "/dashboard" frontend/src

# Check for /frontend/api references (should be 0)
grep -r "/frontend/api" frontend/src

# Check all frontend routes return 200
curl -s -o /dev/null -w "%{http_code}" http://test.localhost:8002/frontend
curl -s -o /dev/null -w "%{http_code}" http://test.localhost:8002/frontend/items
curl -s -o /dev/null -w "%{http_code}" http://test.localhost:8002/frontend/activate-qr
```

---

## Testing Rules

Every new frontend page must be tested for:
1. Load success - returns 200
2. Console errors - no "Invalid URL" errors
3. Valid network requests - API calls go to /api/method/* or /api/resource/*

---

## Files Changed (2025-03-16)

### Frontend Fixes

1. **frontend/src/App.tsx**
   - Changed FrappeProvider url handling to use empty string instead of "/"
   - Added explicit check to exclude "/" from base URL

2. **frontend/src/api/frappe.ts**
   - Changed API base URL handling to use empty string instead of "/"
   - Added explicit check to exclude "/" from base URL
   - Added CSRF token header (X-Frappe-CSRF-Token) to API calls

3. **frontend/src/pages/Settings.tsx**
   - Fixed /dashboard link to use "/" (frontend root)

### Backend Fixes

1. **scanifyme/items/services/item_service.py**
   - Added "Generated" to valid QR code states for activation
   - Updated error message to include all valid states

---

## Known Issues

1. ~~API endpoint `scanifyme.api.get_user_role` not found~~ - RESOLVED (was authentication issue)
2. QR code activation requires specific status - Added "Generated" as valid state

---

## Completed Modules (Phase 2 - 2026-03-16)

### Backend
- ✅ QR Batch management
- ✅ QR Code Tag management
- ✅ QR generation service (token, uid, url, image)
- ✅ Item activation flow
- ✅ Registered Item flow
- ✅ Owner Profile linkage
- ✅ Item Categories

### Frontend
- ✅ React SPA at /frontend
- ✅ Dashboard page
- ✅ Items list page
- ✅ Item detail page
- ✅ Activate QR page
- ✅ Settings page
- ✅ Auth context with Frappe integration
- ✅ API wrapper with CSRF support

---

## Demo Data

### Demo Data Generator
Created a whitelisted admin-only method to generate demo data:

**Command:**
```bash
bench --site test.localhost execute scanifyme.api.demo_data.create_demo_data
```

**Demo Data Created:**
- **Demo User:** demo@scanifyme.app (password: demo123)
- **Demo Owner Profile:** Linked to demo user
- **Item Categories:** Keys, Bag, Wallet, Laptop, Pet
- **QR Batch:** QRB-2026-00003
- **QR Tags:** 6 tags in various states (In Stock, Activated, Suspended, Printed)
- **Registered Items:** 
  - MacBook Pro 14 (Active, linked to activated QR)
  - My House Keys (Draft, no QR linked)

**Demo QR Tokens:**
- In Stock: XYP6TTGG2T, C9M4TSVW2G, KRREMBPWQZ
- Activated: 7B6L98CCFF (linked to MacBook Pro 14)
- Suspended: 252NGFHSHW
- Printed: 56TZDETASD

---

## API Inventory

### Owner/Item APIs
| Method | Purpose |
|--------|---------|
| `scanifyme.items.api.items_api.activate_qr` | Validate and activate QR token |
| `scanifyme.items.api.items_api.create_item` | Create new registered item |
| `scanifyme.items.api.items_api.get_user_items` | Get current user's items |
| `scanifyme.items.api.items_api.get_item_details` | Get item details |
| `scanifyme.items.api.items_api.update_item_status` | Update item status |
| `scanifyme.items.api.items_api.link_item_to_qr` | Link item to QR |
| `scanifyme.items.api.items_api.get_item_categories` | Get all categories |

### Admin/QR APIs
| Method | Purpose |
|--------|---------|
| `scanifyme.qr_management.api.qr_api.create_qr_batch` | Create QR batch |
| `scanifyme.qr_management.api.qr_api.get_qr_batches` | List QR batches |
| `scanifyme.qr_management.api.qr_api.get_qr_tags` | List QR tags |
| `scanifyme.qr_management.api.qr_api.get_qr_preview` | Get QR preview |

### Demo Data APIs
| Method | Purpose |
|--------|---------|
| `scanifyme.api.demo_data.create_demo_data` | Generate demo data |
| `scanifyme.api.demo_data.get_demo_tokens` | Get demo QR tokens |

### Public Portal APIs
| Method | Purpose | Access |
|--------|---------|--------|
| `scanifyme.public_portal.api.public_api.get_public_item_context` | Get public-safe item context | Guest |
| `scanifyme.messaging.api.message_api.submit_finder_message` | Submit message from finder | Guest |

### Recovery APIs
| Method | Purpose | Access |
|--------|---------|--------|
| `scanifyme.recovery.api.recovery_api.get_owner_recovery_cases` | Get owner's recovery cases | Owner |
| `scanifyme.recovery.api.recovery_api.get_recovery_case_details` | Get case details | Owner |
| `scanifyme.recovery.api.recovery_api.get_recovery_case_messages` | Get case messages | Owner |
| `scanifyme.recovery.api.recovery_api.mark_recovery_case_status` | Update case status | Owner |
| `scanifyme.messaging.api.message_api.send_owner_message` | Send message to finder | Owner |

---

## Frontend Routes

| Route | Auth | Purpose |
|-------|------|---------|
| `/frontend` | Required | Main dashboard |
| `/frontend/settings` | Required | Settings management |
| `/frontend/items` | Required | User's registered items |
| `/frontend/items/:id` | Required | Item detail page |
| `/frontend/activate-qr` | Required | QR activation and item creation |
| `/s/<token>` | Public | Public scan portal |

---

## Public Routes

---

## Testing Strategy

### Backend Tests
- Location: `scanifyme/items/tests/test_item_service.py`
- Tests: activate_qr, create_item, link_item_to_qr, get_user_items

### Frontend Tests (Playwright)
- Location: `frontend/tests/scanifyme.spec.ts`
- Config: `frontend/playwright.config.ts`
- Tests:
  - Frontend routes load without crash
  - API endpoints accessible
  - No Invalid URL errors in console
  - No /frontend/api references
  - Public scan page loads
  - Public API returns valid response

### Running Tests
```bash
# Backend tests
cd /home/vineelreddykamireddy/frappe/scanifyme
python -m pytest scanifyme/items/tests/

# Frontend tests
cd /home/vineelreddykamireddy/frappe/scanifyme/apps/scanifyme/frontend
npx playwright test
```

---

## Security Constraints

### Public Access
- Public route `/s/<token>` is accessible without authentication
- Public API `get_public_item_context` uses `allow_guest=True`
- Public API `submit_finder_message` uses `allow_guest=True`

### Protected Access
- Recovery case APIs require authentication
- Owner can only see their own recovery cases
- Permission checks in place for:
  - `get_owner_recovery_cases`
  - `get_recovery_case_details`
  - `get_recovery_case_messages`
  - `mark_recovery_case_status`

### Data Privacy
- Public APIs never expose:
  - Owner email/phone
  - Owner profile internal name
  - Database IDs
  - System metadata
- Only safe public fields returned:
  - public_label
  - recovery_note
  - reward_note
  - item status

### IP Hashing
- Scan events and finder sessions use hashed IP addresses
- Original IP never stored

---

## Environment Requirements

### Services
| Service | Port | Status |
|---------|------|--------|
| Redis Cache | 13002 | Running |
| Redis Queue | 11002 | Running |
| Frappe Web | 8002 | Running |

### URLs
- Desk: http://test.localhost:8002/app
- Frontend: http://test.localhost:8002/frontend
- API: http://test.localhost:8002/api

---

## Bench Validation Procedure

### Starting Bench
```bash
cd /home/vineelreddykamireddy/frappe/scanifyme
bench start
```

### Verify Services
```bash
# Check Redis
redis-cli -p 13002 ping  # Should return PONG
redis-cli -p 11002 ping  # Should return PONG

# Check API
curl -s http://test.localhost:8002/api/method/ping

# Check frontend
curl -s -o /dev/null -w "%{http_code}" http://test.localhost:8002/frontend
```

### Generate Demo Data
```bash
bench --site test.localhost execute scanifyme.api.demo_data.create_demo_data
```

### API Smoke Tests
```bash
# QR Batches
bench --site test.localhost execute scanifyme.qr_management.api.qr_api.get_qr_batches

# QR Tags
bench --site test.localhost execute scanifyme.qr_management.api.qr_api.get_qr_tags

# Demo tokens
bench --site test.localhost execute scanifyme.api.demo_data.get_demo_tokens
```

### Run Frontend Tests
```bash
cd /home/vineelreddykamireddy/frappe/scanifyme/apps/scanifyme/frontend
npx playwright test
```

---

## How to Validate Locally

1. **Start Redis** (if needed):
   ```bash
   redis-server --port 13002 --daemonize yes --dir /tmp --dbfilename dump13002.rdb
   redis-server --port 11002 --daemonize yes --dir /tmp --dbfilename dump11002.rdb
   ```

2. **Start Bench**:
   ```bash
   cd /home/vineelreddykamireddy/frappe/scanifyme
   bench start
   ```

3. **Migrate** (if needed):
   ```bash
   bench --site test.localhost migrate
   ```

4. **Generate Demo Data**:
   ```bash
   bench --site test.localhost execute scanifyme.api.demo_data.create_demo_data
   ```

5. **Validate Public Scan Portal**:
   ```bash
   # Test public token API
   curl "http://test.localhost:8002/api/method/scanifyme.public_portal.api.public_api.get_public_item_context?token=<valid_token>"
   
   # Test public scan page
   curl "http://test.localhost:8002/s/<valid_token>"
   ```

6. **Run Tests**:
   ```bash
   # Frontend tests
   cd frontend && npx playwright test
   ```

---

## Files Created/Updated This Phase

### New DocTypes
1. **Recovery Case** (`scanifyme/recovery/doctype/recovery_case/`)
   - Fields: case_title, qr_code_tag, registered_item, owner_profile, status, timestamps, finder info, notes

2. **Recovery Message** (`scanifyme/recovery/doctype/recovery_message/`)
   - Fields: recovery_case, sender_type, sender_name, message, attachment, timestamps, flags

3. **Scan Event** (`scanifyme/recovery/doctype/scan_event/`)
   - Fields: qr_code_tag, registered_item, token, scanned_on, ip_hash, user_agent, route, status, recovery_case

4. **Finder Session** (`scanifyme/recovery/doctype/finder_session/`)
   - Fields: session_id, qr_code_tag, timestamps, ip_hash, user_agent, status

### New Backend Modules
1. **Public Portal** (`scanifyme/public_portal/`)
   - `services/public_scan_service.py` - Token resolution, public context, scan events
   - `api/public_api.py` - Public API endpoints

2. **Recovery** (`scanifyme/recovery/`)
   - `services/recovery_service.py` - Case management, status updates
   - `api/recovery_api.py` - Owner recovery case APIs

3. **Messaging** (`scanifyme/messaging/`)
   - `services/message_service.py` - Message handling, session management
   - `api/message_api.py` - Finder and owner messaging APIs

### New Public Page
1. **Public Scan Portal** (`scanifyme/www/public_portal/scan.py`)
   - Handles `/s/<token>` route
   - Renders safe public item information
   - Includes finder message form

2. **Public Template** (`scanifyme/templates/pages/public_portal/scan.html`)
   - Displays item info, recovery note, reward note
   - Finder message submission form
   - Error state handling

### Updated Files
1. **demo_data.py** - Added recovery case, scan event, finder session, recovery messages
2. **scan.py** (moved to www/public_portal/) - Fixed route handling
3. **hooks.py** - Route mapping for public scan portal
4. **scanifyme.spec.ts** - Added public portal tests

---

## Testing This Phase

### Backend Tests
- Token resolution: Valid/invalid tokens
- Public API: Safe field filtering
- Scan event creation
- Recovery case creation and status updates
- Messaging flow

### Frontend Tests (Playwright)
- `/s/<token>` loads for valid token
- `/s/<token>` shows error for invalid token
- Public API returns valid response

### API Tests
- `get_public_item_context` - Guest access, safe fields
- `submit_finder_message` - Creates case/message
- `get_owner_recovery_cases` - Protected access
- `get_recovery_case_messages` - Protected access

---

## Known Constraints

1. **Authentication**: Frontend requires authentication via Frappe Desk. Unauthenticated users are redirected to `/login`.

2. ~~**Public Finder Page**: The `/s/<token>` public scan page exists in route config but the actual web page handler is not fully implemented yet.~~ - RESOLVED

3. **Item Count Sync**: Owner Profile `update_item_counts()` method exists but is not automatically called on item changes.

4. ~~**QR Scan Tracking**: Scan history is not fully implemented - `last_scan_at` is set but no scan logging exists.~~ - RESOLVED (Scan Event DocType created)

5. **Ownership Transfer**: Ownership Transfer DocType exists but API endpoints are not exposed.

---

## Files Created/Updated This Phase

1. **New File: `scanifyme/api/demo_data.py`**
   - Demo data generator for testing
   - create_demo_data() - Creates demo user, categories, QR batch, tags, items
   - get_demo_tokens() - Retrieves demo QR tokens

2. **Updated: `frontend/tests/scanifyme.spec.ts`**
   - Updated Playwright tests for frontend validation
   - Tests for route loading, API access, console errors

3. **Updated: `frontend/playwright.config.ts`**
   - Updated baseURL to test.localhost:8002
   - Simplified to single chromium project
