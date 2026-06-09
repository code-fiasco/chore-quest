# Chore Quest – Architecture

## Overview
Two-person household chore gamification PWA. Built to run locally via Docker Compose, deployable to Google Cloud Run + Cloud SQL with minimal changes.

## Stack
- **Frontend:** SvelteKit (Vite, served on :5173)
- **Backend:** FastAPI (Python 3.12, served on :8000)
- **Database:** PostgreSQL 16
- **Email (local):** MailHog (SMTP :1025, web UI :8025)
- **Scheduling:** APScheduler embedded in FastAPI

## Services (docker-compose.yml)
| Service   | Port  | Purpose                        |
|-----------|-------|--------------------------------|
| frontend  | 5173  | SvelteKit dev server           |
| backend   | 8000  | FastAPI REST API               |
| db        | 5432  | PostgreSQL                     |
| mailhog   | 8025  | Email preview (local only)     |

## Backend Layout
```
backend/app/
├── main.py          # FastAPI app, CORS, router registration
├── config.py        # Settings from .env via pydantic-settings
├── database.py      # SQLAlchemy engine and session
├── models/          # SQLAlchemy ORM models (one file per entity)
├── routes/          # FastAPI routers (one file per domain)
├── services/        # Business logic (scoring, streaks, badges, email)
└── scheduler.py     # APScheduler jobs (daily challenges, emails)
```

## Domain Model (from PRD §28)
- **User** – display name, avatar, email, password hash, role (member/admin), household
- **Household** – name, timezone, admin user
- **Task** – name, description, frequency (daily/weekly/monthly), points, category, room, required/optional
- **TaskInstance** – generated per period per task, tracks completion state
- **Completion** – who completed which instance and when
- **Badge** – definitions and user awards
- **Leaderboard** – weekly/monthly/lifetime snapshots

## Key Rules (from PRD)
- First completion wins; task instance locks
- Undo recalculates all derived data
- Required tasks affect streaks; optional do not
- Streak: at least one required task per day
- Daily challenges generated at 06:00 household timezone
- Daily email at 22:00, weekly email Monday 08:00
- History is immutable (§23)
- First registered user becomes admin

## Cloud Migration Path
To move from local to Google Cloud:
1. Replace `db` container → Cloud SQL (Postgres)
2. Replace `backend` container → Cloud Run
3. Replace `frontend` container → Cloud Run or Firebase Hosting
4. Replace `mailhog` → Resend or SendGrid
5. Set environment variables in Cloud Run; no application code changes needed
