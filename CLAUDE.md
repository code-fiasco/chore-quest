# Chore Quest – Claude Code Instructions

This file is read automatically by Claude Code at the start of every session.

## Project Summary
Chore Quest is a two-person household chore gamification PWA.
- Backend: FastAPI (Python 3.12) on port 8000
- Frontend: SvelteKit on port 5173
- Database: PostgreSQL 16
- All services run via Docker Compose

## Key files to read before working
- `ARCHITECTURE.md` – stack, layout, domain model, migration path
- `TASKS.md` – implementation backlog with status

## Rules
1. Do not change docker-compose.yml or .env.example without being asked.
2. All business logic goes in `backend/app/services/`, not in routes.
3. Routes should be thin – validate input, call a service, return a response.
4. Never hardcode secrets or credentials.
5. Keep TASKS.md updated when completing tasks.
6. When creating a new DB model, always create the corresponding Alembic migration.
7. History (Completion records) must never be altered or deleted (PRD §23).
8. The first registered user becomes household admin automatically (PRD §4).
9. Always back up the database before applying any migrations in production:
   docker compose exec db pg_dump -U chorequest chorequest > backup.sql

## Running the project locally
```bash
docker compose up --build
```
- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Frontend: http://localhost:5173
