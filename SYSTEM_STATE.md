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
