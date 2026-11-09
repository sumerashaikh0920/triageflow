# Deploying TriageFlow (portfolio-friendly)

Two routes. Pick **A** if you want the exact stack from `docker-compose.yml` live with one command. Pick **B** if you want a free/cheap split deployment, which is usually enough for a portfolio link.

> **Read first: what is actually live-able today**
> - The **frontend** currently runs on in-app mock data with a role-picker login. It makes no API calls, so a visitor can use the whole UI with only the frontend deployed.
> - The **backend** is production-shaped (JWT, roles, Alembic, PostgreSQL) but uses its own mock predictor; the **ML service** runs next to it and is not called by the backend yet.
> - So the minimum live demo is the frontend alone. Deploy the backend and ML service when you want to show the APIs (`/docs`) or the retraining pipeline.

## Security rules for any public deployment

| Rule | Why |
|---|---|
| Set a long random `JWT_SECRET` (`openssl rand -hex 32`) | The compose default is public in the repo. |
| Set a strong `POSTGRES_PASSWORD` (URL-safe characters) | Same. |
| Never expose the **ML service** directly to the internet | `/retrain/run`, `/models/*/activate` and `/feedback` have **no authentication**. Keep it on a private network, or put a gateway in front that checks a key (then store the header as the `ML_SERVICE_AUTH_HEADER` secret). |
| Treat the seeded accounts as public | `admin@triageflow.dev / Password123!` is in the README and `app/seed.py`. If the backend is reachable from the internet, anyone can log in as admin. Either keep the backend private, or seed once, change the passwords, and set `SEED_ON_STARTUP=false`. |
| Set `CORS_ORIGINS` to your real frontend origin(s) only | Default is localhost. |
| Serve everything over HTTPS | Caddy (route A) and every platform in route B do this automatically. |

---

## Route A: one VM with Docker Compose + Caddy

Works on any Linux VM (cloud free tiers, a small VPS). Plan for about 2 vCPU / 4 GB RAM: the ML image bundles PyTorch and is the heaviest container. I have not measured its memory use, so check `docker stats` after first boot.

1. **Create the VM**, point DNS at it (for example `demo.example.com`), and open only ports 22, 80 and 443 in the cloud firewall / security group.
   Docker publishes ports by editing iptables, so host firewalls such as `ufw` do **not** reliably block the compose ports. Use the cloud-level firewall.
2. **Install Docker + the Compose plugin** (see docs.docker.com/engine/install).
3. **Get the code and configure**
   ```bash
   git clone https://github.com/sumerashaikh0920/triageflow.git
   cd triageflow
   cp .env.example .env
   # edit .env: JWT_SECRET, POSTGRES_PASSWORD, CORS_ORIGINS=https://demo.example.com
   ```
4. **Start the stack**
   ```bash
   docker compose up -d --build --wait
   docker compose ps          # all four services should be "healthy"
   ```
5. **Add HTTPS with Caddy** (`apt install caddy`, or run it as a container), `/etc/caddy/Caddyfile`:
   ```
   demo.example.com {
       reverse_proxy localhost:3000
   }
   # Optional: expose the API docs publicly. Omit to keep the backend private.
   api.example.com {
       reverse_proxy localhost:8000
   }
   ```
   `sudo systemctl reload caddy`. Do **not** add a block for the ML service.
6. **Update later**: `git pull && docker compose up -d --build`. Data lives in the `pg_data`, `ml_models` and `ml_feedback_exports` volumes and survives rebuilds. `docker compose down -v` deletes them.
7. **Back up** the database: `docker compose exec db pg_dump -U triageflow triageflow > backup.sql` (and `triageflow_ml` for the ML service).

---

## Route B: split free-tier deployment

Platforms change their free plans often. Check current limits (sleep behaviour, RAM, database expiry) before relying on one.

### 1. Frontend, static hosting (Vercel, Netlify or Cloudflare Pages)

| Setting | Value |
|---|---|
| Root directory | `frontend` |
| Install | `npm install` (or `npm ci` once `package-lock.json` is committed) |
| Build command | `npm run build` |
| Output directory | `dist` |

The app uses client-side routing, so add a rewrite of every path to `/index.html`:
- Netlify: create `frontend/public/_redirects` containing `/*  /index.html  200`
- Vercel: `frontend/vercel.json` containing `{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }`
- Cloudflare Pages: SPA fallback is on by default when there is no top-level `404.html`.

That alone gives you a working live demo.

### 2. Backend + database (Render, Fly.io, Railway, or similar, plus managed Postgres such as Neon or Supabase)

- Deploy `backend/` from its `Dockerfile` (the entrypoint runs migrations, then seeds if `SEED_ON_STARTUP=true`, then starts uvicorn on port 8000).
- Set environment variables: `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS` (your frontend URL), `ENV=production`, `SEED_ON_STARTUP`.
- **`DATABASE_URL` must start with `postgresql+psycopg2://`.** Providers hand out `postgres://...` or `postgresql://...`; rewrite the scheme or SQLAlchemy will not use the installed driver. Managed databases usually also need `?sslmode=require` on the end.
- Health check path: `/health` (liveness) or `/ready` (also checks the database).

### 3. ML service (optional)

- Deploy `ml-service/` from its `Dockerfile`; port 8000; health check path `/health`.
- Give it its **own database** (`DATABASE_URL`, any Postgres) and a **persistent disk mounted at `/srv/app/models`**. Model artifacts are files on disk; the registry rows are in Postgres. Without the disk, a restart leaves registry rows that point at artifacts that no longer exist.
- It needs the most memory of the three services (PyTorch). If a free plan is too small, leave it out of the live demo and run it locally for screenshots.
- Keep it private or gated (see the security table above).

---

## GitHub Actions setup

| Item | Where | Needed for |
|---|---|---|
| CI | nothing to configure | Runs on every push/PR. Marking the jobs as required in branch protection is recommended. |
| `ML_SERVICE_URL` | Secret (optional) | Retraining workflows target your deployed ML service. **Unset = dry run inside the runner**, which proves the pipeline works but deploys nothing. |
| `ML_SERVICE_AUTH_HEADER` | Secret (optional) | Header line sent on every call, if you front the ML service with a gateway. Example: `X-Api-Key: <value>`. |

A GitHub-hosted runner can only reach a service that is reachable from the public internet, which collides with "keep the ML service private". Either put an authenticated gateway in front of it, or run `scripts/retrain_via_api.sh` from a machine on its private network (for example from cron on the VM in route A) and rely on the dry-run workflow in GitHub for CI evidence.

### Retraining workflows

- `retrain-scheduled.yml` runs weekly (Mondays 03:00 UTC) and can be started by hand: Actions, then **Retrain (scheduled / manual)**, then **Run workflow** (choose `baseline` or `transformer`, optionally `force`).
- `retrain-on-feedback.yml` runs when a `feedback-approved` dispatch event arrives. Send one with:
  ```bash
  GITHUB_REPOSITORY=sumerashaikh0920/triageflow GITHUB_TOKEN=<fine-grained PAT> \
    ./scripts/notify_feedback_approved.sh 25 baseline
  ```
  The PAT needs "Contents: read and write" on this repository. Keep it in the secret store of whatever sends the event, never in the repo.
- Both end with a **candidate registered as pending**. Nothing is approved or deployed automatically; a person approves and activates (`POST /models/{version}/approve`, then `/activate`) after reading the run summary. A candidate that regresses beyond `RETRAIN_REGRESSION_TOLERANCE` cannot be approved or activated at all.
- GitHub only runs scheduled workflows on the default branch and pauses them after 60 days without repository activity.
