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

---

## APIs

### Whitelisted Methods

| Method | Module | Access | Purpose |
|--------|--------|--------|---------|
| `get_settings` | scanifyme_core | Authenticated | Get singleton settings |
| `get_public_settings` | scanifyme_core | Guest | Get public settings |
| `update_settings` | scanifyme_core | Admin | Update settings |
| `get_user_role` | api | Authenticated | Get current user's role |

### Public Token Format
QR codes use secure tokens in URL: `/s/<secure_token>`
Example: `https://scanifyme.app/s/X7K9M4PQ`

---

## Frontend Routes

| Route | Auth | Purpose |
|-------|------|---------|
| `/dashboard` | Auth | Main dashboard |
| `/settings` | Auth | Settings management |
| `/` | Auth | Redirects to dashboard |

**Note**: Unauthenticated users are redirected to Frappe Desk login (`/login`)

---

## Frontend Structure

```
src/
├── api/
│   └── frappe.ts          # API wrapper (useFrappe hook)
├── contexts/
│   └── AuthContext.tsx   # Auth context provider
├── hooks/                 # Custom React hooks (future)
├── pages/
│   ├── Dashboard.tsx     # Dashboard page
│   └── Settings.tsx      # Settings page
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

---

## Next Steps (Future Prompts)

1. Implement QR code generation and management
2. Create item doctype with ownership
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
