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

### QR Services

| Function | Module | Purpose |
|----------|--------|---------|
| `generate_qr_token()` | qr_management.services.qr_service | Generate random 8-12 char token |
| `generate_qr_uid()` | qr_management.services.qr_service | Generate human-readable UID |
| `generate_qr_url()` | qr_management.services.qr_service | Generate public URL /s/token |
| `generate_qr_image()` | qr_management.services.qr_service | Generate QR image using File API |
| `generate_qr_batch()` | qr_management.services.qr_service | Create batch of QR codes |
| `get_public_qr()` | qr_management.services.qr_service | Get public QR by token |

### Public Token Format
QR codes use secure tokens in URL: `/s/<secure_token>`
Example: `https://scanifyme.app/s/X7K9M4PQ`

---

## Frontend Routes

| Route | Auth | Purpose |
|-------|------|---------|
| `/dashboard` | Auth | Main dashboard with QR stats |
| `/settings` | Auth | Settings management |
| `/items` | Auth | Items management (placeholder) |
| `/activate-qr` | Auth | QR code activation (placeholder) |
| `/` | Auth | Redirects to dashboard |

**Note**: Unauthenticated users are redirected to Frappe Desk login (`/login`)

---

## Frontend Structure

```
src/
├── api/
│   └── frappe.ts          # API wrapper (QR functions added)
├── contexts/
│   └── AuthContext.tsx   # Auth context provider
├── hooks/                 # Custom React hooks (future)
├── pages/
│   ├── Dashboard.tsx     # Dashboard page (enhanced)
│   ├── Settings.tsx      # Settings page
│   ├── Items.tsx         # Items placeholder page
│   └── ActivateQR.tsx    # Activate QR placeholder page
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
2. Create Registered Item DocType
3. Build recovery workflow
4. Implement messaging between finder and owner
5. Add notification system
6. Create public scan page for guests

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
