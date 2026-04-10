# Civic Complaint Management System — Complete Project Overview

## 1. What This Project Is

A full-stack web application where **citizens report civic issues** (encroachments, garbage dumps, road damage, water issues, drainage, street lights, etc.) and **government officers manage and resolve them**. Complaints that remain unresolved for 3 days are **automatically escalated** to higher authorities via a background task scheduler.

**Tech Stack:**

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 18 + Vite 5 | SPA with Tailwind CSS |
| Backend | FastAPI (Python 3) | REST API with async MongoDB |
| Database | MongoDB 7 | Document storage (Motor async driver) |
| Cache/Broker | Redis 7 | Celery message broker |
| Task Queue | Celery 5 | Auto-escalation background jobs |
| Image Storage | Cloudinary | Complaint/resolution photos |
| Maps | Leaflet + react-leaflet | Interactive location picker |
| Charts | Recharts | Admin dashboard analytics |
| Auth | JWT (HS256) | Stateless token-based auth |

---

## 2. Directory Structure

```
D:\miniproject\
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry, CORS, routers, lifecycle
│   │   ├── seed.py                  # Seeds initial super_admin account
│   │   ├── api/
│   │   │   ├── auth.py              # /api/auth/* — register, login, profile
│   │   │   ├── complaints.py        # /api/complaints/* — CRUD, images, nearby
│   │   │   └── admin.py             # /api/admin/* — dashboard, assign, users, officers
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic BaseSettings from .env
│   │   │   ├── database.py          # Motor MongoDB client singleton
│   │   │   ├── deps.py              # JWT auth dependencies, role checker
│   │   │   └── security.py          # bcrypt hashing, JWT create/decode
│   │   ├── models/
│   │   │   ├── user.py              # UserRole enum, User/Token Pydantic models
│   │   │   └── complaint.py         # ComplaintCategory/Status/Priority enums, models
│   │   ├── schemas/
│   │   │   ├── user.py              # Request/Response DTOs for users
│   │   │   └── complaint.py         # Request/Response DTOs for complaints
│   │   ├── services/
│   │   │   ├── user_service.py      # User CRUD, get_all_officers
│   │   │   ├── complaint_service.py # Complaint CRUD, escalation, geospatial, stats
│   │   │   └── cloudinary_service.py# Image upload/delete to Cloudinary
│   │   └── tasks/
│   │       ├── celery_app.py        # Celery config, beat schedule (hourly)
│   │       └── escalation.py        # Auto-escalation Celery task
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── main.jsx                 # Entry point, Leaflet icon fix
│   │   ├── App.jsx                  # React Router, ProtectedRoute, role redirect
│   │   ├── index.css                # Global styles, Leaflet container
│   │   ├── pages/
│   │   │   ├── Login.jsx            # Email/password login
│   │   │   ├── Register.jsx         # New user registration
│   │   │   ├── UserDashboard.jsx    # Citizen's complaint list with filters
│   │   │   ├── OfficerDashboard.jsx # Officer's assigned complaints + stats
│   │   │   ├── AdminDashboard.jsx   # Analytics, pie chart, assign officers
│   │   │   ├── SuperAdminDashboard.jsx # User management, create officers
│   │   │   ├── ComplaintForm.jsx    # New complaint with map + image upload
│   │   │   └── ComplaintDetail.jsx  # Full complaint view with timeline
│   │   ├── components/
│   │   │   ├── Layout.jsx           # Nav header with role-based links
│   │   │   ├── ComplaintCard.jsx    # Complaint summary card
│   │   │   ├── StatCard.jsx         # Metric card (title, value, icon)
│   │   │   ├── StatusBadge.jsx      # Color-coded status pill
│   │   │   └── LocationPicker.jsx   # Leaflet map click-to-pin + geolocation
│   │   ├── context/
│   │   │   └── AuthContext.jsx      # Global auth state (login, register, logout)
│   │   ├── services/
│   │   │   ├── api.js               # Axios instance with JWT interceptor
│   │   │   └── complaints.js        # All complaint/admin API functions
│   │   └── utils/
│   │       └── leaflet-icons.js     # Fix Leaflet marker icon CDN paths
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   └── Dockerfile
├── docker-compose.yml               # 6 services: mongodb, redis, backend, celery_worker, celery_beat, frontend
├── .env                             # Active environment variables (gitignored)
├── .env.example                     # Template for environment variables
└── CLAUDE.md                        # AI assistant project instructions
```

---

## 3. Database Schema

### 3.1 `users` Collection

| Field | Type | Description |
|-------|------|-------------|
| `_id` | ObjectId | Auto-generated |
| `email` | string | Unique, used for login |
| `name` | string | Display name |
| `phone` | string \| null | Optional phone number |
| `hashed_password` | string | bcrypt hash |
| `role` | string | `"user"` \| `"local_officer"` \| `"super_admin"` |
| `assigned_area` | dict \| null | GeoJSON area for officers (not actively used) |
| `is_active` | boolean | Account active flag |
| `created_at` | datetime | UTC timestamp |
| `updated_at` | datetime | UTC timestamp |

**Roles:**
- `user` — Citizen who submits complaints
- `local_officer` — Frontline officer assigned to resolve complaints
- `super_admin` — Top-level admin, manages users/officers, receives escalated complaints

**Seed account:** `admin@civicfix.com` / `admin123` (role: super_admin), created via `python -m app.seed`

### 3.2 `complaints` Collection

| Field | Type | Description |
|-------|------|-------------|
| `_id` | ObjectId | Auto-generated |
| `ticket_id` | string | Format: `CMP-YYYYMMDD-NNNN` (auto-generated sequential) |
| `title` | string | Complaint title (min 5 chars) |
| `description` | string | Detailed description (min 10 chars) |
| `category` | string | One of: `encroachment`, `garbage_dump`, `road_damage`, `water_issue`, `drainage`, `street_light`, `other` |
| `status` | string | `pending` → `in_progress` → `resolved` OR `pending` → `escalated` |
| `priority` | string | `low`, `medium` (default), `high`, `urgent` |
| `location` | GeoJSON Point | `{"type": "Point", "coordinates": [longitude, latitude]}` |
| `address` | string \| null | Human-readable address |
| `images` | string[] | Cloudinary URLs of complaint photos |
| `submitted_by` | ObjectId | Reference to `users._id` |
| `assigned_to` | ObjectId \| null | Reference to `users._id` (officer) |
| `escalated` | boolean | Whether complaint has been escalated |
| `escalated_to` | string \| null | Not actively populated |
| `escalation_level` | int | Number of times escalated (starts at 0) |
| `resolution_notes` | string \| null | Notes added when resolving |
| `resolution_images` | string[] | Cloudinary URLs of after-resolution photos |
| `created_at` | datetime | UTC timestamp |
| `updated_at` | datetime | UTC timestamp |
| `resolved_at` | datetime \| null | Set when status becomes `resolved` |
| `escalated_at` | datetime \| null | Set when first escalated |

**Index:** `2dsphere` on `location` field for geospatial `$near` queries.

---

## 4. API Endpoints (Complete Reference)

### 4.1 Authentication — `/api/auth`

| Method | Path | Auth Required | Roles | Description |
|--------|------|---------------|-------|-------------|
| POST | `/api/auth/register` | No | — | Register new user (always role=`user`) |
| POST | `/api/auth/login` | No | — | Login, returns JWT + user info |
| GET | `/api/auth/me` | Yes | Any | Get current user profile |
| PUT | `/api/auth/me` | Yes | Any | Update name/phone |

**Auth mechanism:** JWT Bearer token in `Authorization` header. Token expires in 7 days. Contains `sub` (email), `role`, `exp`.

### 4.2 Complaints — `/api/complaints`

| Method | Path | Auth Required | Roles | Description |
|--------|------|---------------|-------|-------------|
| POST | `/api/complaints/` | Yes | Any | Create new complaint |
| POST | `/api/complaints/{id}/images` | Yes | Any | Upload complaint images (multipart) |
| POST | `/api/complaints/{id}/resolution-images` | Yes | Any | Upload resolution images (multipart) |
| GET | `/api/complaints/my` | Yes | Any | Get current user's submitted complaints |
| GET | `/api/complaints/assigned` | Yes | Any | Get complaints assigned to officer |
| GET | `/api/complaints/nearby` | Yes | Any | Geospatial search: `?lon=&lat=&radius_km=` |
| GET | `/api/complaints/{id}` | Yes | Any | Get single complaint details |
| PUT | `/api/complaints/{id}` | Yes | Any | Update complaint status/resolution |

**Complaint creation flow:**
1. POST `/api/complaints/` with `{title, description, category, latitude, longitude, address}`
2. Backend generates ticket_id (`CMP-YYYYMMDD-NNNN`), sets status=`pending`, priority=`medium`
3. Optionally POST `/api/complaints/{id}/images` with multipart form files (uploaded to Cloudinary)

**Nearby complaints:** Uses MongoDB `$near` with 2dsphere index. Default radius: 5km.

### 4.3 Admin — `/api/admin`

| Method | Path | Auth Required | Roles | Description |
|--------|------|---------------|-------|-------------|
| GET | `/api/admin/complaints` | Yes | officer, super_admin | List all complaints (paginated, filterable) |
| GET | `/api/admin/dashboard` | Yes | officer, super_admin | Dashboard statistics |
| GET | `/api/admin/stats/categories` | Yes | officer, super_admin | Complaint counts by category |
| PUT | `/api/admin/complaints/{id}/assign` | Yes | officer, super_admin | Assign complaint to officer |
| PUT | `/api/admin/complaints/{id}/status` | Yes | officer, super_admin | Update complaint status |
| GET | `/api/admin/users` | Yes | super_admin | List all users (paginated) |
| GET | `/api/admin/officers` | Yes | officer, super_admin | List all officers |
| POST | `/api/admin/officers` | Yes | super_admin | Create new officer |

**Query params for GET `/api/admin/complaints`:** `page`, `limit`, `status`, `category`, `escalated_only`

**Assign flow:** PUT body `{"officer_id": "..."}` → sets `assigned_to` and changes status to `in_progress`

---

## 5. Frontend Routing & Pages

| Route | Page Component | Access | Description |
|-------|---------------|--------|-------------|
| `/login` | Login.jsx | Public | Email/password login form |
| `/register` | Register.jsx | Public | Registration form (name, email, phone, password) |
| `/` | RoleBasedRedirect | Authenticated | Redirects: user→`/dashboard`, officer→`/admin`, super_admin→`/admin` |
| `/dashboard` | UserDashboard.jsx | user | Citizen's complaints with status filter |
| `/officer` | OfficerDashboard.jsx | local_officer, super_admin | Assigned complaints + stat cards |
| `/admin` | AdminDashboard.jsx | local_officer, super_admin | Analytics, pie chart, recent complaints, assign officers |
| `/super-admin` | SuperAdminDashboard.jsx | super_admin | User list, officer list, create officer modal |
| `/complaints/new` | ComplaintForm.jsx | Authenticated | Form with map picker + image upload |
| `/complaints/:id` | ComplaintDetail.jsx | Authenticated | Full detail view with timeline |

**Route protection:** `ProtectedRoute` component wraps routes, checks `AuthContext` for user and role.

**State management:** React Context (`AuthContext`) for auth. Local `useState` for all page-level data. No Redux or external state library.

**HTTP client:** Axios instance in `services/api.js` with:
- Base URL from `VITE_API_URL` env var (default: `http://localhost:8000`)
- Auto-attaches `Authorization: Bearer <token>` from localStorage
- 401 interceptor → clears token, redirects to `/login`

**Styling:** Tailwind CSS with custom colors:
- `trust-blue` #2563eb (primary buttons, links)
- `engagement-blue` #3b82f6 (hover states)
- `growth-green` #10b981 (resolved, success)
- `caution-orange` #f59e0b (pending, warning)
- `alert-red` #ef4444 (escalated, danger)

**Icons:** `@heroicons/react/24/outline` — no emojis used anywhere.

**Maps:** Leaflet via `react-leaflet`. Default center: Bangalore [12.9716, 77.5946]. LocationPicker component supports click-to-pin and browser geolocation API.

---

## 6. Escalation System (How It Works)

### Current Flow

```
Citizen submits complaint
        │
        ▼
  Status: PENDING
  escalated: false
  escalation_level: 0
        │
        ├─── Super Admin manually assigns to Local Officer ───▶ Status: IN_PROGRESS
        │                                                              │
        │                                                    Officer resolves ──▶ RESOLVED
        │
        └─── 3 days pass, still PENDING ───▶
                │
                ▼
         Celery Beat (hourly) triggers check_escalations()
                │
                ▼
         Status: ESCALATED
         escalated: true
         escalation_level: 1
         escalated_at: <timestamp>
                │
                ▼
         Super Admin notified (email currently commented out)
```

### Escalation Details

- **Trigger:** Celery beat schedule fires `check_escalations` every 1 hour
- **Condition:** `status == "pending"` AND `escalated == false` AND `created_at < now - 3 days`
- **Action:** Sets `escalated=true`, `status="escalated"`, increments `escalation_level`, sets `escalated_at`
- **Notification:** Code fetches super_admins from DB but email sending is **commented out** (line 45 in `escalation.py`)
- **Configuration:** `ESCALATION_DAYS=3` in `.env`

### Current Limitations

1. **No auto-assignment** — Complaints sit unassigned until a super_admin manually assigns them
2. **No auto-reassignment on escalation** — Escalation just flags the complaint; doesn't reassign to a different/higher officer
3. **Single escalation tier** — Once escalated, there's no further level to escalate to
4. **`assigned_area` on officers is unused** — The field exists in the user model for GeoJSON area assignment but no code uses it for auto-matching complaints to officers by location
5. **No notifications actually sent** — Email sending is stubbed out
6. **`escalated_to` field exists in model but is never populated** by any code

---

## 7. Role-Based Access Control Matrix

| Action | user | local_officer | super_admin |
|--------|------|--------------|-------------|
| Register | Yes (as user) | — | — |
| Login | Yes | Yes | Yes |
| View own profile | Yes | Yes | Yes |
| Update own profile | Yes | Yes | Yes |
| Submit complaint | Yes | Yes | Yes |
| View own complaints | Yes | Yes | Yes |
| View assigned complaints | — | Yes | Yes |
| View any complaint detail | Yes (own only) | Yes (assigned) | Yes (all) |
| Update complaint status | — | Yes (assigned) | Yes (all) |
| Upload images | Yes (own) | Yes (assigned) | Yes (all) |
| View all complaints | — | Yes | Yes |
| View dashboard stats | — | Yes | Yes |
| Assign officer to complaint | — | Yes | Yes |
| List all users | — | — | Yes |
| Create officer account | — | — | Yes |
| List officers | — | Yes | Yes |

**Note:** Route protection uses `require_role(*roles)` dependency from `app/core/deps.py`. It decodes the JWT, fetches the user from DB, and checks the role field.

---

## 8. Docker Deployment

`docker-compose.yml` defines 6 services:

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| `mongodb` | mongo:7 | 27017 | Database with named volume |
| `redis` | redis:7-alpine | 6379 | Message broker with named volume |
| `backend` | Custom | 8000 | FastAPI app, depends on mongo+redis healthy |
| `celery_worker` | Custom | — | Background task worker |
| `celery_beat` | Custom | — | Scheduler (hourly escalation checks) |
| `frontend` | Custom | 3000→5173 | React app (Vite preview server) |

All services use `unless-stopped` restart policy. Environment variables injected from host.

---

## 9. Environment Variables

| Variable | Example | Description |
|----------|---------|-------------|
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `DATABASE_NAME` | `complaint_db` | Database name |
| `SECRET_KEY` | `your-jwt-secret` | JWT signing key |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` | Token expiry (7 days) |
| `CLOUDINARY_CLOUD_NAME` | `mycloud` | Cloudinary account name |
| `CLOUDINARY_API_KEY` | `123456` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | `abcdef` | Cloudinary API secret |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | Celery results |
| `SMTP_HOST` | `smtp.gmail.com` | Email server (not actively used) |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | — | SMTP username |
| `SMTP_PASSWORD` | — | SMTP password |
| `ESCALATION_DAYS` | `3` | Days before auto-escalation |

Frontend also needs: `VITE_API_URL` (default: `http://localhost:8000`)

---

## 10. Key Backend Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.109.0 | Web framework |
| uvicorn[standard] | 0.27.0 | ASGI server |
| motor | 3.3.2 | Async MongoDB driver |
| pymongo | 4.6.1 | MongoDB driver |
| python-jose[cryptography] | 3.3.0 | JWT token handling |
| passlib[bcrypt] | 1.7.4 | Password hashing |
| bcrypt | 4.2.1 | Bcrypt algorithm |
| python-multipart | 0.0.6 | File upload parsing |
| pydantic[email] | 2.5.3 | Data validation |
| pydantic-settings | 2.1.0 | Settings from env vars |
| celery | 5.3.6 | Distributed task queue |
| redis | 5.0.1 | Redis client |
| cloudinary | 1.39.0 | Image cloud storage |
| geopy | 2.4.1 | Geocoding utilities |

## 11. Key Frontend Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| react | 18.2.0 | UI library |
| react-dom | 18.2.0 | React DOM renderer |
| react-router-dom | 6.22.0 | Client-side routing |
| axios | 1.6.7 | HTTP client |
| react-leaflet | 4.2.1 | React map components |
| leaflet | 1.9.4 | Map rendering |
| @heroicons/react | 2.1.1 | Icon library (outline style) |
| recharts | 2.12.0 | Chart library |
| tailwindcss | 3.4.1 | Utility-first CSS |

---

## 12. What's Built vs What's Stubbed

### Fully Working
- User registration, login, JWT auth
- Complaint CRUD (create, read, update status)
- Image upload to Cloudinary (complaint + resolution photos)
- Interactive map location picker with geolocation
- Officer assignment by admin
- Auto-escalation via Celery (flagging only)
- Dashboard with stats and category pie chart
- Role-based access control (3 roles)
- Docker Compose full-stack deployment
- Nearby complaints geospatial search

### Stubbed / Incomplete
- Email notifications (SMTP config exists, sending code commented out)
- `assigned_area` on officers (field exists, never used for auto-matching)
- `escalated_to` field (model field exists, never populated)
- `send_notification` Celery task (just prints to console)
- No multi-level escalation (only one escalation step)
- No auto-assignment of complaints to officers based on location/area
- No real-time updates (no WebSocket, polling, or SSE)
- No password reset flow
- No complaint commenting/discussion system
- No audit log for status changes
