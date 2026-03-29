# Complaint Management System - Project Analysis

## Overview
A civic issue reporting platform where citizens can report problems like encroachments, garbage dumps, and road damage. The system features **auto-escalation** that flags unresolved complaints to higher authorities after 3 days.

## Architecture

### Tech Stack
| Layer      | Technology                          |
|------------|-------------------------------------|
| Frontend   | React + Tailwind CSS + React Leaflet|
| Backend    | FastAPI (Python)                    |
| Database   | MongoDB (with GeoJSON)              |
| Cache/Queue| Redis (Celery broker)               |
| Image Store| Cloudinary                          |
| Auth       | JWT (python-jose + passlib)         |

### Project Structure
```
miniproject/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── api/                 # Route handlers
│   │   │   ├── auth.py          # Register, login, profile
│   │   │   ├── complaints.py    # CRUD + image upload
│   │   │   └── admin.py         # Dashboard + officer management
│   │   ├── core/
│   │   │   ├── config.py        # Settings from .env
│   │   │   ├── database.py      # Motor (async MongoDB)
│   │   │   ├── security.py      # JWT + bcrypt
│   │   │   └── deps.py          # Auth dependencies, role checks
│   │   ├── models/              # Pydantic data models
│   │   │   ├── user.py          # User, roles, tokens
│   │   │   └── complaint.py     # Complaint, status, location
│   │   ├── schemas/             # Request/Response schemas
│   │   ├── services/            # Business logic
│   │   │   ├── user_service.py
│   │   │   ├── complaint_service.py
│   │   │   └── cloudinary_service.py
│   │   └── tasks/
│   │       ├── celery_app.py    # Celery config + beat schedule
│   │       └── escalation.py    # Auto-escalation background job
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Full page views
│   │   ├── hooks/               # Custom React hooks
│   │   ├── services/            # API client functions
│   │   ├── context/             # Auth context
│   │   └── utils/               # Helpers
│   └── (React app files)
└── project_analysis.md
```

## Database Design

### Users Collection
```json
{
  "email": "citizen@example.com",
  "name": "John Doe",
  "phone": "+91-9876543210",
  "hashed_password": "$2b$12$...",
  "role": "user | local_officer | super_admin",
  "assigned_area": { "type": "Polygon", "coordinates": [...] },
  "is_active": true,
  "created_at": "ISO date"
}
```

### Complaints Collection
```json
{
  "ticket_id": "CMP-20260323-0001",
  "title": "Garbage dump near park",
  "description": "Large garbage dump accumulating...",
  "category": "garbage_dump",
  "location": {
    "type": "Point",
    "coordinates": [77.5946, 12.9716]
  },
  "address": "Near Central Park, Bangalore",
  "images": ["https://res.cloudinary.com/..."],
  "status": "pending | in_progress | resolved | escalated",
  "priority": "low | medium | high | urgent",
  "submitted_by": "user_id",
  "assigned_to": "officer_id",
  "escalated": false,
  "escalation_level": 0,
  "resolution_notes": "Area cleaned and sanitized",
  "resolution_images": [],
  "created_at": "ISO date",
  "updated_at": "ISO date",
  "resolved_at": "ISO date",
  "escalated_at": "ISO date"
}
```
**Index:** 2dsphere on `location` field for geo queries.

## API Endpoints

### Auth (`/api/auth`)
| Method | Endpoint        | Description         | Auth Required |
|--------|-----------------|---------------------|---------------|
| POST   | /register       | Register new user   | No            |
| POST   | /login          | Login & get JWT     | No            |
| GET    | /me             | Get current user    | Yes           |
| PUT    | /me             | Update profile      | Yes           |

### Complaints (`/api/complaints`)
| Method | Endpoint                      | Description           | Auth Required |
|--------|-------------------------------|-----------------------|---------------|
| POST   | /                             | Submit complaint      | Yes (User)    |
| POST   | /{id}/images                  | Upload complaint img  | Yes (User)    |
| POST   | /{id}/resolution-images       | Upload proof of work  | Yes (Officer) |
| GET    | /my                           | My complaints         | Yes (User)    |
| GET    | /nearby?lon=&lat=&radius=     | Nearby complaints     | Yes           |
| GET    | /{id}                         | Get complaint detail  | Yes           |
| PUT    | /{id}                         | Update status         | Yes (Officer) |

### Admin (`/api/admin`)
| Method | Endpoint                        | Description        | Role Required    |
|--------|---------------------------------|--------------------|------------------|
| GET    | /dashboard                      | Dashboard stats    | Officer / Admin  |
| GET    | /stats/categories               | Category breakdown | Officer / Admin  |
| GET    | /complaints                     | All complaints     | Officer / Admin  |
| PUT    | /complaints/{id}/assign         | Assign to officer  | Officer / Admin  |
| PUT    | /complaints/{id}/status         | Update status      | Officer / Admin  |
| GET    | /officers                       | List officers      | Officer / Admin  |
| POST   | /officers                       | Create officer     | Super Admin      |
| GET    | /users                          | List all users     | Super Admin      |

## Auto-Escalation System

The core feature. Runs as a Celery periodic task:

1. **Trigger:** Every hour, Celery beat fires `check_escalations` task
2. **Logic:** Finds all complaints where `status == "pending"` AND `created_at < now - 3 days`
3. **Action:**
   - Sets `escalated = true`
   - Changes `status = "escalated"`
   - Increments `escalation_level`
   - Records `escalated_at` timestamp
   - (Optional) Sends email notification to super admins
4. **Dashboard impact:** Escalated complaints show in red on the admin dashboard

## Roles & Access Control

| Feature              | User | Local Officer | Super Admin |
|----------------------|------|---------------|-------------|
| Submit complaint     | Yes  | Yes           | Yes         |
| View own complaints  | Yes  | Yes           | Yes         |
| View all complaints  | No   | Yes           | Yes         |
| Assign officers      | No   | Yes           | Yes         |
| Resolve complaints   | No   | Yes           | Yes         |
| Create officers      | No   | No            | Yes         |
| Manage users         | No   | No            | Yes         |
| View dashboard       | No   | Yes           | Yes         |

## Getting Started

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
# Copy .env.example to .env and fill in values
uvicorn app.main:app --reload --port 8000
```

### Celery Worker (for auto-escalation)
```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
celery -A app.tasks.celery_app beat --loglevel=info
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
