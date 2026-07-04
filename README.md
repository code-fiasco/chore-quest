# Chore Quest

Gamified household chores PWA for two people. Complete tasks, earn points, unlock badges, and compete on leaderboards.

## Stack

| Layer    | Technology                          |
|----------|-------------------------------------|
| Frontend | SvelteKit (static build + nginx)    |
| Backend  | FastAPI (Python 3.12)               |
| Database | PostgreSQL 16                       |
| Email    | SMTP (IONOS)                        |

## Quick start

1. Copy environment variables and edit as needed:

   ```bash
   cp .env.example .env   # if .env.example exists; otherwise create .env
   ```

2. Start the stack:

   ```bash
   docker compose up -d --build
   ```

3. Open the app:

   - **Production (Cloudflare Tunnel):** https://your-domain.example
   - **Local via tunnel origin:** http://127.0.0.1:5173

The frontend is bound to `127.0.0.1:5173` only — it is not exposed on the LAN. Postgres and the API are internal to the Docker network.

## Environment variables

Key settings in `.env`:

| Variable       | Description                                      |
|----------------|--------------------------------------------------|
| `DB_USER`      | Postgres username                                |
| `DB_PASSWORD`  | Postgres password                                |
| `DB_NAME`      | Postgres database name                           |
| `SECRET_KEY`   | JWT signing key (long random string)             |
| `APP_ENV`      | `production` or `local`                          |
| `FRONTEND_URL` | Public URL, e.g. `https://cq.example.com`        |
| `SMTP_*`       | SMTP host, credentials, and sender addresses     |

In production set `APP_ENV=production` and a real `FRONTEND_URL`. This enables secure cookies, disables Swagger, and tightens CORS.

## Architecture

- **nginx** serves the built SvelteKit app and proxies `/api/*` to FastAPI.
- **FastAPI** handles auth, tasks, scoring, badges, and scheduled jobs (APScheduler).
- **PostgreSQL** stores all application data.

See [ARCHITECTURE.md](ARCHITECTURE.md) for domain model and backend layout.

## Production deployment (Cloudflare Tunnel)

Typical setup: `cloudflared` runs on the host and forwards to the frontend container:

```yaml
# /etc/cloudflared/config.yml
ingress:
  - hostname: cq.example.com
    service: http://localhost:5173
  - service: http_status:404
```

Docker Compose publishes the frontend on `127.0.0.1:5173:8080` so cloudflared can reach it without exposing the port on the network interface.

TLS termination and rate limiting are handled at Cloudflare.

## Security

The production Docker setup includes:

- Non-root users in backend and frontend containers
- `cap_drop: [ALL]` and `no-new-privileges`
- Read-only root filesystem with scoped tmpfs mounts
- CPU/memory limits (1 core, 512 MB per app container)
- Isolated `chorequest` Docker network
- nginx security headers (CSP, X-Frame-Options, etc.)
- Swagger/OpenAPI disabled when `APP_ENV=production`
- Secure httpOnly session cookies in production
- Registration capped at two users per household

Postgres and the API are not published to the host.

## Auth

- Register, login, logout, password reset via email
- First registered user becomes household admin
- Maximum two users — registration closes automatically when full
- Password reset links go to `/password-reset/confirm?token=...`

## Database migrations

Migrations run automatically on backend startup (`alembic upgrade head`).

To back up before manual migration work:

```bash
docker compose exec db pg_dump -U chorequest chorequest > backup.sql
```

## Development

For local development with hot reload, use the dev Dockerfiles or run services directly:

```bash
# Backend (from backend/)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (from frontend/)
npm install && npm run dev
```

Swagger docs are available at http://localhost:8000/docs when `APP_ENV=local`.

## Useful commands

```bash
docker compose ps
docker compose logs -f backend
docker compose up -d --build
docker compose down
```
