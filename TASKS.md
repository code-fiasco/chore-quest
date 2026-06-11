# Chore Quest – Task Backlog

Use this file to track implementation progress. Feed relevant sections to Claude Code at the start of each session.

Legend: ⬜ Not started | 🔄 In progress | ✅ Done

---

## Phase 1 – Foundation

- ✅ **DB-01** Create SQLAlchemy models: User, Household (models/user.py, models/household.py)
- ✅ **DB-02** Create SQLAlchemy models: Task, TaskInstance, Completion (models/task.py)
- ✅ **DB-03** Create SQLAlchemy models: Badge, UserBadge, Leaderboard (models/gamification.py)
- ✅ **DB-04** Set up Alembic migrations (alembic.ini, first migration)
- ✅ **DB-05** Create database.py with SQLAlchemy engine and get_db dependency

## Phase 2 – Authentication

- ✅ **AUTH-01** POST /auth/register – create user, first user becomes admin, create household
- ✅ **AUTH-02** POST /auth/login – return JWT session token
- ✅ **AUTH-03** POST /auth/logout
- ✅ **AUTH-04** POST /auth/password-reset/request – send reset email
- ✅ **AUTH-05** POST /auth/password-reset/confirm – apply new password
- ✅ **AUTH-06** get_current_user dependency for protected routes
- ✅ **AUTH-07** Avatar selection from predefined list (e.g. Tiger, Kitten, etc.)

## Phase 3 – Task Management (Admin)

- ✅ **TASK-01** GET /tasks – list all tasks for household
- ✅ **TASK-02** POST /tasks – create task (admin only)
- ✅ **TASK-03** PUT /tasks/{id} – edit task (admin only)
- ✅ **TASK-04** DELETE /tasks/{id} – delete task (admin only)
- ✅ **TASK-05** Task instance generation logic – daily/weekly/monthly scheduling
- ✅ **TASK-06** Monthly task distribution across 4 weeks
- ✅ **TASK-07** Category CRUD (admin only)
- ✅ **TASK-08** Task sort_order column, reorder endpoint, admin drag-and-drop

## Phase 4 – Completion & Scoring

- ✅ **SCORE-01** POST /tasks/{id}/complete – first-completion-wins, lock instance, award points
- ✅ **SCORE-02** POST /tasks/{id}/undo – undo own completion, recalculate all derived data
- ✅ **SCORE-03** Points calculation: base 10pts + bonuses
- ✅ **SCORE-04** Bonus: room completion sweep
- ✅ **SCORE-05** Bonus: category sweep
- ✅ **SCORE-06** Bonus: deep clean bonus
- ✅ **SCORE-07** Bonus: weekly goal completion
- ✅ **SCORE-08** Bonus: streak milestones
- ✅ **SCORE-09** Daily / weekly / monthly / lifetime score aggregation

## Phase 5 – Gamification

- ✅ **GAME-01** Streak tracking – one required task per day maintains streak
- ✅ **GAME-02** Daily challenge generation at 06:00 household timezone (3 tasks selected)
- ✅ **GAME-03** Weekly goal configuration (admin) and tracking
- ✅ **GAME-04** Badge definitions (34 visible badges)
- ✅ **GAME-05** Secret badge definitions (8 secret badges incl. The Completionist)
- ✅ **GAME-06** Badge award logic and triggers (all 42 badges checked after each completion)
- ✅ **GAME-07** Leaderboard snapshots – weekly, monthly, lifetime

## Phase 6 – Frontend (SvelteKit)

- ✅ **FE-01** SvelteKit project init inside /frontend
- ✅ **FE-02** API client setup (fetch wrapper pointing to backend)
- ✅ **FE-03** Auth pages: Register, Login, Password Reset
- ✅ **FE-04** Home/dashboard: today's tasks (daily/weekly/monthly sections)
- ✅ **FE-05** Task completion UI with undo
- ✅ **FE-06** Daily challenges widget
- ✅ **FE-07** Leaderboard page
- ✅ **FE-08** Badges page
- ✅ **FE-09** Statistics page
- ✅ **FE-10** Admin panel: task/category management, weekly goals, master reset
- ✅ **FE-11** PWA manifest and service worker

## Phase 7 – Email

- ✅ **EMAIL-01** Email service abstraction (local: MailHog SMTP, prod: Resend API)
- ✅ **EMAIL-02** Daily summary email template (22:00)
- ✅ **EMAIL-03** Weekly summary email template (Monday 08:00)
- ✅ **EMAIL-04** APScheduler jobs for both emails, timezone-aware

## Phase 8 – Polish & Deployment Prep

- ✅ **OPS-01** docker-compose.prod.yml overrides (no MailHog, env vars for Cloud)
- ✅ **OPS-02** Environment-based config switching (local vs prod)
- ✅ **OPS-03** Production Dockerfile for frontend (static build + Nginx)
- ⬜ **OPS-04** Cloud SQL connection instructions
- ⬜ **OPS-05** Cloud Run deployment notes

---

## Notes for Claude Code sessions

Always start a session by saying:
> "Read ARCHITECTURE.md and TASKS.md. I want to work on [TASK-ID]. Here is the relevant section of the PRD: [paste PRD section]"

Keep TASKS.md updated as you complete items.
