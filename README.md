# Chore Quest

Gamified household chores PWA for two people. Complete tasks, earn points, unlock badges, and compete on leaderboards.

## Stack

| Layer      | Technology                       |
|------------|----------------------------------|
| Frontend   | SvelteKit (static build + nginx) |
| Backend    | FastAPI (Python 3.12)            |
| Database   | PostgreSQL 16                    |
| Email      | SMTP (e.g. IONOS)                |
| Scheduling | APScheduler (in FastAPI)         |
| Deploy     | Docker Compose + Cloudflare Tunnel |

## Requirements

- Docker Engine and Docker Compose v2
- A host that can run containers (Linux recommended for production)
- SMTP credentials for password-reset and notification emails
- Optional for public HTTPS: [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) (`cloudflared`)

## Install and deploy (production)

### 1. Clone the repository

```bash
git clone git@github.com:code-fiasco/chore-quest.git
cd chore-quest
```

### 2. Create the environment file

There is no committed `.env` (secrets stay local). Create one in the project root:

```bash
cat > .env <<'EOF'
# Postgres (used by docker-compose for the db service)
DB_USER=chorequest
DB_PASSWORD=change-me-to-a-strong-password
DB_NAME=chorequest

# App
SECRET_KEY=replace-with-a-long-random-string
APP_ENV=production
FRONTEND_URL=https://cq.example.com

# SMTP (password reset + daily/weekly emails)
SMTP_HOST=smtp.ionos.co.uk
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
EMAIL_FROM=noreply@example.com
EMAIL_FROM_NAME=Chore Quest
EMAIL_REPLY_TO=noreply@example.com
EOF
```

Generate a strong `SECRET_KEY`:

```bash
openssl rand -hex 32
```

| Variable | Required | Description |
|----------|----------|-------------|
| `DB_USER` | Yes | Postgres username |
| `DB_PASSWORD` | Yes | Postgres password |
| `DB_NAME` | Yes | Postgres database name |
| `SECRET_KEY` | Yes | JWT signing key (long random string) |
| `APP_ENV` | Yes | `production` or `local` |
| `FRONTEND_URL` | Yes | Public app URL used for CORS and email links |
| `SMTP_HOST` | Yes | SMTP server hostname |
| `SMTP_PORT` | Yes | Usually `587` |
| `SMTP_USE_TLS` | Yes | `true` for STARTTLS |
| `SMTP_USERNAME` | Yes | SMTP auth username |
| `SMTP_PASSWORD` | Yes | SMTP auth password |
| `EMAIL_FROM` | Yes | From address on outbound mail |
| `EMAIL_FROM_NAME` | No | Display name (default: Chore Quest) |
| `EMAIL_REPLY_TO` | No | Reply-To; defaults to `EMAIL_FROM` |

In production set `APP_ENV=production` and a real `FRONTEND_URL`. That enables secure cookies, disables Swagger/OpenAPI, and tightens CORS.

### 3. Build and start

```bash
docker compose up -d --build
```

This starts three services on the `chorequest` Docker network:

| Service    | Role                                      | Host access                          |
|------------|-------------------------------------------|--------------------------------------|
| `db`       | PostgreSQL 16                             | Internal only                        |
| `backend`  | FastAPI + migrations + scheduler          | Internal only                        |
| `frontend` | nginx serving the SvelteKit build         | `127.0.0.1:5173` → container `:8080` |

Check status:

```bash
docker compose ps
docker compose logs -f backend
```

Migrations run automatically on backend startup (`alembic upgrade head`).

### 4. Open the app

- **On the host:** http://127.0.0.1:5173
- **Public HTTPS:** via Cloudflare Tunnel (next section)

The first registered user becomes household admin. Registration closes after two users.

### 5. Update or restart later

```bash
git pull
docker compose up -d --build
```

```bash
docker compose down          # stop
docker compose restart       # restart without rebuild
docker compose logs -f       # follow all logs
```

## Production deployment with Cloudflare Tunnel

Typical layout: Docker Compose on a private host, `cloudflared` on the same host forwarding only to localhost.

1. Install and authenticate `cloudflared`, then create a tunnel for your hostname.
2. Point ingress at the published frontend port:

```yaml
# /etc/cloudflared/config.yml
tunnel: <your-tunnel-id>
credentials-file: /etc/cloudflared/<your-tunnel-id>.json

ingress:
  - hostname: cq.example.com
    service: http://localhost:5173
  - service: http_status:404
```

3. Ensure `.env` has matching values:

```bash
APP_ENV=production
FRONTEND_URL=https://cq.example.com
```

4. Start the stack, then start the tunnel service:

```bash
docker compose up -d --build
sudo systemctl enable --now cloudflared
```

Docker Compose publishes the frontend on `127.0.0.1:5173:8080` so cloudflared can reach it without exposing the port on the LAN. TLS and rate limiting are handled at Cloudflare. Postgres and the API are not published to the host.

## Architecture

- **nginx** serves the built SvelteKit app and proxies `/api/*` to FastAPI.
- **FastAPI** handles auth, tasks, scoring, badges, admin resets, and scheduled jobs.
- **PostgreSQL** stores all application data.

See [ARCHITECTURE.md](ARCHITECTURE.md) for domain model and backend layout. See [TASKS.md](TASKS.md) for the implementation backlog.

## Features (admin)

From the in-app Admin panel (admin role only):

- Manage tasks, categories, and weekly goals
- Enable/disable daily challenges and set challenge count (1–5)
- **Clear progress** — wipe completions, points, badges, and scores; keep tasks
- **Master reset** — wipe tasks and game data (categories and accounts kept)

## Security

The production Docker setup includes:

- Non-root users in backend and frontend containers
- `cap_drop: [ALL]` and `no-new-privileges`
- Read-only root filesystem with scoped tmpfs mounts
- CPU/memory limits (1 core, 512 MB per app container)
- Isolated `chorequest` Docker network
- nginx security headers (strict CSP without `unsafe-inline` / `unsafe-eval`, X-Frame-Options, etc.)
- Swagger/OpenAPI disabled when `APP_ENV=production`
- Secure httpOnly session cookies in production
- Registration capped at two users per household

## Auth

- Register, login, logout, password reset via email
- First registered user becomes household admin
- Maximum two users — registration closes automatically when full
- Password reset links go to `/password-reset/confirm?token=...`

## Database backup and restore

Back up before risky changes or production migrations:

```bash
docker compose exec -T db pg_dump -U chorequest chorequest > backup.sql
```

Restore:

```bash
docker compose exec -T db psql -U chorequest chorequest < backup.sql
```

(Use the `DB_USER` / `DB_NAME` values from your `.env` if they differ.)

## Local development

For hot reload outside the production images:

```bash
# Terminal 1 – Postgres (or use docker compose up db -d)
# Terminal 2 – Backend
cd backend
# Point DATABASE_URL at your Postgres, APP_ENV=local, FRONTEND_URL=http://localhost:5173
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3 – Frontend
cd frontend
npm install
npm run dev
```

Swagger is available at http://localhost:8000/docs when `APP_ENV=local`.

## Useful commands

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose up -d --build
docker compose down
docker compose exec backend alembic current
```
