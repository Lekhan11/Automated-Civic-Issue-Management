# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Civic Complaint Management System - citizens report issues (encroachments, garbage dumps, road damage), and unresolved complaints auto-escalate to higher authorities after 3 days.

## Commands

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configure MongoDB, Redis, Cloudinary, JWT secret
uvicorn app.main:app --reload --port 8000  # Dev server
```

### Celery (Auto-escalation)
```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info  # Worker
celery -A app.tasks.celery_app beat --loglevel=info    # Scheduler (runs hourly)
```

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev    # Dev server at http://localhost:5173
npm run build  # Production build
```

## Architecture

### Backend Structure
- `app/api/` - Route handlers (auth, complaints, admin)
- `app/core/` - Config, database (Motor async MongoDB), security (JWT), dependencies
- `app/models/` - Pydantic models with enums (UserRole, ComplaintStatus, ComplaintCategory)
- `app/schemas/` - Request/Response DTOs
- `app/services/` - Business logic (user_service, complaint_service, cloudinary_service)
- `app/tasks/` - Celery tasks for auto-escalation

### Frontend Structure
- `src/pages/` - Route-level components (Login, Register, UserDashboard, AdminDashboard, ComplaintForm, ComplaintDetail)
- `src/components/` - Reusable UI (Layout, ComplaintCard, StatusBadge, StatCard, LocationPicker)
- `src/context/AuthContext.jsx` - JWT auth state management
- `src/services/` - API client functions

### Key Patterns

**Role-Based Access Control**: Three roles - `user`, `local_officer`, `super_admin`. Use `require_role()` dependency from `app/core/deps.py` to protect routes.

**GeoJSON Locations**: Complaints use MongoDB GeoJSON Point format `{"type": "Point", "coordinates": [lon, lat]}`. Create 2dsphere index for geospatial queries.

**Auto-Escalation**: Celery beat schedules `check_escalations` task hourly. Finds complaints where `status == pending` AND `created_at < now - 3 days`, sets `escalated=true`, `status=escalated`.

**Color Palette**: trust-blue (#2563eb), engagement-blue (#3b82f6), growth-green (#10b981), caution-orange (#f59e0b), alert-red (#ef4444). Use Heroicons (outline) for icons, not emojis.

## Environment Variables

Backend `.env` requires: `MONGODB_URL`, `DATABASE_NAME`, `SECRET_KEY`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `REDIS_URL`, `CELERY_BROKER_URL`.
