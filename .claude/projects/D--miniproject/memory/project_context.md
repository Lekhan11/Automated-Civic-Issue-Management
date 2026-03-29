---
name: Complaint Management System - Session Context
description: Complete context for the Civic Complaint Management System project for reuse in future sessions
type: project
---

# Complaint Management System - Project Context

## Project Overview
A civic issue reporting platform where citizens can report problems (encroachments, garbage dumps, road damage). Features **auto-escalation** that flags unresolved complaints to higher authorities after 3 days.

## Tech Stack
- **Frontend:** React + Vite + Tailwind CSS + React Leaflet
- **Backend:** FastAPI (Python)
- **Database:** MongoDB with GeoJSON for geospatial data
- **Image Storage:** Cloudinary
- **Background Jobs:** Celery + Redis for auto-escalation
- **Auth:** JWT (python-jose + bcrypt)

## Project Structure
```
D:/miniproject/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── api/
│   │   │   ├── auth.py          # Auth endpoints
│   │   │   ├── complaints.py    # Complaint CRUD + assigned endpoint
│   │   │   └── admin.py         # Admin dashboard, user management
│   │   ├── core/                # Config, database, security, deps
│   │   ├── models/              # Pydantic models
│   │   ├── schemas/             # Request/Response DTOs
│   │   ├── services/            # Business logic
│   │   └── tasks/               # Celery tasks for escalation
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/          # Layout, ComplaintCard, StatusBadge, StatCard, LocationPicker
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── UserDashboard.jsx
│   │   │   ├── OfficerDashboard.jsx    # Complaints assigned TO officer
│   │   │   ├── AdminDashboard.jsx      # All complaints + stats
│   │   │   ├── SuperAdminDashboard.jsx # User/officer management
│   │   │   ├── ComplaintForm.jsx
│   │   │   └── ComplaintDetail.jsx
│   │   ├── context/AuthContext.jsx
│   │   ├── services/            # API client functions
│   │   └── utils/leaflet-icons.js
│   └── Dockerfile
├── docker-compose.yml
├── .env
└── CLAUDE.md
```

## Docker Services
| Service | Port | Description |
|---------|------|-------------|
| mongodb | 27017 | Database |
| redis | 6379 | Celery broker |
| backend | 8000 | FastAPI API |
| celery_worker | - | Background task worker |
| celery_beat | - | Scheduler (hourly escalation check) |
| frontend | 3000 | React app |

## Commands to Run
```bash
cd D:/miniproject
docker compose up -d           # Start all services
docker compose down            # Stop all services
docker compose logs -f backend # View backend logs
docker compose up --build -d   # Rebuild and restart
```

## Key Fixes Made This Session

### 1. bcrypt Version Incompatibility
- **Issue:** `passlib 1.7.4` incompatible with `bcrypt 5.x`
- **Fix:** Pinned `bcrypt==4.2.1` in requirements.txt

### 2. Empty Status Filter Error
- **Issue:** Frontend sent `status=` (empty string) causing enum validation error
- **Fix:** Changed admin.py to accept `Optional[str]` and convert to enum manually, treating empty strings as None

### 3. Officer Dashboard Not Showing Assigned Complaints
- **Issue:** `/officer` page was using `getMyComplaints()` which fetches complaints SUBMITTED BY user
- **Fix:**
  - Created new endpoint `/api/complaints/assigned` that fetches complaints WHERE `assigned_to = current_user`
  - Updated OfficerDashboard.jsx to use `getAssignedComplaints()`

### 4. Leaflet Map Not Displaying
- **Issue:** Various null pointer errors with react-leaflet
- **Fix:** Rewrote LocationPicker.jsx using react-leaflet with proper component structure (MapEvents, MapController)

## User Roles & Pages

| Role | Default Page | Access |
|------|--------------|--------|
| user | `/dashboard` | Own complaints only |
| local_officer | `/officer` | Assigned complaints + `/admin` |
| super_admin | `/super-admin` | Everything + user management |

## Test Credentials
- **Super Admin:** `senthillekhan2005@gmail.com` (password from registration)
- Create officers via `/super-admin` page when logged in as super admin

## API Endpoints Summary

### Auth (`/api/auth`)
- POST `/register` - Register user
- POST `/login` - Login, get JWT
- GET `/me` - Current user profile

### Complaints (`/api/complaints`)
- POST `/` - Create complaint
- GET `/my` - Complaints submitted BY user
- GET `/assigned` - Complaints assigned TO user (for officers)
- GET `/{id}` - Complaint details
- PUT `/{id}` - Update status

### Admin (`/api/admin`)
- GET `/dashboard` - Stats
- GET `/complaints` - All complaints (filterable)
- PUT `/complaints/{id}/assign` - Assign to officer
- GET `/officers` - List officers
- POST `/officers` - Create officer (super admin only)
- GET `/users` - List users (super admin only)

## Environment Variables (.env)
- `MONGODB_URL=mongodb://mongodb:27017`
- `DATABASE_NAME=complaint_db`
- `SECRET_KEY=<jwt-secret>`
- `CLOUDINARY_CLOUD_NAME=dlgvgipwj`
- `CLOUDINARY_API_KEY=563351941692551`
- `CLOUDINARY_API_SECRET=zhVsTzzFZWQHPMgc6_c5dybEfJo`
- `REDIS_URL=redis://redis:6379/0`
- `ESCALATION_DAYS=3`

## Color Palette
- Trust Blue: `#2563eb`
- Engagement Blue: `#3b82f6`
- Growth Green: `#10b981`
- Caution Orange: `#f59e0b`
- Alert Red: `#ef4444`

## Pending/Known Issues
- Map may still have display issues in some browsers - check Leaflet CSS is loaded
- Email notifications for escalation not implemented (placeholder in code)

## How to Apply This Context
1. Read this file to understand project state
2. Run `docker compose up -d` to start services
3. Access frontend at http://localhost:3000
4. Access API docs at http://localhost:8000/docs
