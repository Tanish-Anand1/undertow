# Undertow

Watch keywords across Hacker News, GitHub, and X. Classify posts. Surface them in a live feed and a daily digest. Reddit is wired but waiting on Data API approval.

Each unique keyword is crawled once, then matched to every watchlist that shares it. Posts are deduplicated by `(platform, external_id)`. Classification is stored on the post, not on each match.

## Stack

- **API:** FastAPI (does not crawl inline)
- **Workers:** Redis + RQ, separate queues: `hn`, `github`, `x`, `reddit`, `digest`
- **Clock:** `python -m app.clock` enqueues scheduled ingest/digest
- **DB:** Postgres 16
- **Frontend:** React + Vite

## Local run

### 1. Postgres + Redis

```bash
docker compose up -d
```

Postgres is on **5433**. Redis is on **6379**.

### 2. Backend

```bash
cd backend
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
```

Terminal A (API):

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal B (workers):

```bash
python -m app.worker
```

Equivalent:

```bash
rq worker hn github x reddit digest --url redis://localhost:6379/0
```

Terminal C (optional, scheduled enqueue):

```bash
python -m app.clock
```

### 3. Frontend

```bash
cd frontend
pnpm install
pnpm run dev -- --host 127.0.0.1 --port 5173
```

- http://127.0.0.1:5173/ landing
- http://127.0.0.1:5173/app product

## Deploy

- **Frontend (Vercel):** https://undertow-zeta.vercel.app
- **GitHub:** https://github.com/Tanish-Anand1/undertow
- **Backend (Render):** open https://dashboard.render.com/blueprint/new and connect that repo. It uses `render.yaml` (API, worker, clock, Redis, Postgres).

After Render is up, set:

- `CORS_ORIGINS=https://undertow-zeta.vercel.app`
- `PUBLIC_BASE_URL=https://undertow-zeta.vercel.app`
- LLM / X / SendGrid / Google OAuth secrets in the Render dashboard
- Google redirect URI: `https://undertow-api.onrender.com/auth/google/callback`

Vercel `VITE_API_URL` is already set to `https://undertow-api.onrender.com`. If Render gives you a different hostname, update that env and redeploy.

Create an OAuth client in Google Cloud Console (Web application). Authorized redirect URI:

`http://127.0.0.1:8000/auth/google/callback`

Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` in `.env`. The app button **Continue with Google** hits `/auth/google/start`.

## Auth

Email + password, bcrypt, JWT. Optional email verification (`REQUIRE_EMAIL_VERIFY=true`). Password reset: `POST /auth/forgot-password` then `POST /auth/reset-password`. Login is rate-limited.

Local fixture `founder@example.com` / `password123` still works if that user exists. New accounts can sign up without it.

## Guardrails

- Max active keywords per user: `MAX_KEYWORDS_PER_USER` (default 15)
- Manual Scans: unlimited, no cooldown. Scheduled crawls are separate.
- Empty digest: skipped (`DIGEST_SKIP_EMPTY=true`)

`POST /ingest/run` enqueues jobs and returns `{id, status, total_jobs, finished_jobs}`. Poll `GET /ingest/{id}`. Circuit state is on `GET /health`.

## Deploy (Render)

`render.yaml` defines API, worker, clock, Redis, and Postgres. Set secrets in the dashboard (JWT `SECRET_KEY`, NVIDIA/OpenRouter/Fireworks, X keys, SendGrid, `CORS_ORIGINS`, `PUBLIC_BASE_URL`, `REQUIRE_EMAIL_VERIFY`). Point your domain at the web service. Add a free uptime check against `GET /health`.

Do not commit secrets. Rotate anything that ever lived in chat or a local `.env` before a public launch.

## API

- `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- `POST /auth/forgot-password`, `POST /auth/reset-password`, `POST /auth/verify-email`
- `POST /watchlists`, `GET /watchlists`, `DELETE /watchlists/{id}`
- `GET /feed`, `GET /digest`, `GET /stats`
- `POST /ingest/run`, `GET /ingest/{id}`
- `POST /posts/{id}/draft-reply`
- `GET /health`
