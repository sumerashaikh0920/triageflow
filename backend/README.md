# TriageFlow Backend

FastAPI + PostgreSQL backend for **TriageFlow**, an AI-powered customer-support ticket
triage platform. This folder is self-contained — it doesn't touch `frontend/` or
`ml-service/` in the rest of the repo, and only speaks HTTP/JSON so any frontend
(the existing React + TypeScript app) can consume it.

## Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2 (2.0-style `Mapped` models)
- Alembic (migrations)
- PostgreSQL 16
- Pydantic v2
- JWT auth (access + refresh tokens) with bcrypt password hashing
- pytest + httpx (`TestClient`) for automated tests
- Docker / docker-compose (API + Postgres only — no frontend container here)

## Folder structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app, CORS, router registration
│   ├── config.py                # Settings (reads .env)
│   ├── database.py              # SQLAlchemy engine/session/Base
│   ├── security.py              # Password hashing + JWT create/verify
│   ├── dependencies.py          # get_current_user, require_roles(...)
│   ├── seed.py                  # Demo accounts + sample data
│   ├── core/
│   │   ├── constants.py         # Shared enums (roles, statuses, etc.)
│   │   └── exceptions.py        # AppError + frontend-friendly error handler
│   ├── models/                  # SQLAlchemy ORM models (11 tables)
│   ├── schemas/                 # Pydantic request/response models
│   ├── routers/                 # One file per API area (see below)
│   └── services/
│       ├── ml_stub.py           # Mock ML predictor behind BasePredictor interface
│       ├── ticket_service.py    # Ticket creation + prediction orchestration
│       └── audit_service.py     # Audit log writer
├── alembic/                     # Migrations
│   └── versions/0001_initial_schema.py
├── tests/                       # pytest suite (36 tests)
├── requirements.txt
├── .env.example
├── Dockerfile
├── entrypoint.sh                # Waits for DB, runs migrations, optional seed
├── docker-compose.yml           # api + db services
└── README.md
```

## Data model (11 tables)

`users`, `teams`, `tickets`, `ticket_messages`, `ticket_predictions`,
`feedback_corrections`, `routing_rules`, `sla_events`, `model_versions`,
`integrations`, `audit_logs`.

Every ticket, when created, is run through the ML stub and gets a
`ticket_predictions` row with: `category`, `subcategory`, `urgency`, `sentiment`,
`confidence`, `predicted_team`, `model_version`, `explanation`, `predicted_at`.
The ticket's own `category`/`urgency` fields start out equal to the prediction and
can be overridden later by agents via the feedback endpoints.

## Roles

- **agent** — works tickets, submits feedback
- **team_lead** — everything an agent can do, plus manage routing rules and view all users
- **admin** — full access: manage users, teams, integrations, settings

## API surface

| Area | Routes |
|---|---|
| Auth | `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me` |
| Users | `GET /users`, `GET /users/{id}`, `PATCH /users/{id}` (admin) |
| Teams | `GET /teams`, `POST /teams` (admin), `PATCH /teams/{id}` (admin) |
| Tickets | `GET /tickets` (search/filter/sort/paginate), `POST /tickets`, `GET /tickets/{id}`, `PATCH /tickets/{id}`, `POST /tickets/{id}/assign`, `POST /tickets/{id}/status`, `POST /tickets/{id}/messages`, `GET /tickets/{id}/history` |
| Feedback | `GET /feedback`, `POST /feedback/correct-category`, `POST /feedback/mark-urgency`, `POST /feedback/accept-prediction` |
| Dashboard | `GET /dashboard/summary` |
| Routing | `GET /routing/queue`, `GET/POST /routing/rules`, `PATCH /routing/rules/{id}` |
| SLA | `GET /sla/monitor`, `GET /sla/events` |
| Model metrics | `GET /models/versions`, `GET /models/metrics` |
| Integrations | `GET /integrations`, `PATCH /integrations/{id}` (admin) |
| Settings | `GET /settings`, `PATCH /settings` (admin) |
| Health | `GET /health` (liveness), `GET /ready` (readiness — checks DB) |

Full interactive docs (OpenAPI/Swagger) are always available at **`/docs`** once
the server is running, and the raw schema at **`/openapi.json`**.

Errors are returned in a consistent, frontend-friendly shape:
```json
{ "error": { "code": "not_found", "message": "Ticket not found" } }
```

## Option A: Run with Docker (recommended, easiest)

This starts PostgreSQL and the API together, runs migrations automatically, and
seeds demo data.

```bash
cd backend
cp .env.example .env        # optional — docker-compose sets sane defaults itself
docker compose up --build
```

The API will be live at **http://localhost:8000** (docs at `http://localhost:8000/docs`).
On first boot, `entrypoint.sh` waits for Postgres, runs `alembic upgrade head`, and
(because `SEED_ON_STARTUP=true` in `docker-compose.yml`) seeds demo accounts and
sample tickets.

To stop everything: `docker compose down` (add `-v` to also wipe the database volume).

## Option B: Run locally without Docker

1. **Install PostgreSQL 16** locally (or use any reachable Postgres instance) and
   create a database + user matching `.env`, e.g.:
   ```sql
   CREATE USER triageflow WITH PASSWORD 'triageflow';
   CREATE DATABASE triageflow OWNER triageflow;
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   cd backend
   python3.12 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # edit .env if your Postgres isn't on localhost:5432 with the default credentials
   ```

4. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Seed demo data (optional but recommended):**
   ```bash
   python -m app.seed
   ```

6. **Start the API:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

Visit **http://localhost:8000/docs** to explore and try every endpoint.

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `ENV` | `development` / `production` | `development` |
| `DEBUG` | Verbose errors | `true` |
| `PROJECT_NAME` | Shown in `/` and OpenAPI title | `TriageFlow` |
| `DATABASE_URL` | SQLAlchemy connection string | `postgresql+psycopg2://triageflow:triageflow@localhost:5432/triageflow` |
| `JWT_SECRET` | Signing key for JWTs — **change in production** | dev value only |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `CORS_ORIGINS` | Comma-separated allowed origins for the React frontend | `http://localhost:3000,http://localhost:5173` |
| `SEED_ON_STARTUP` | If `true`, the Docker entrypoint seeds demo data on boot | `false` |

See `.env.example` for a ready-to-copy file.

## Demo accounts

Created by `python -m app.seed` (or automatically in Docker):

| Role | Email | Password |
|---|---|---|
| Admin | `admin@triageflow.dev` | `Password123!` |
| Team Lead | `lead@triageflow.dev` | `Password123!` |
| Agent | `agent@triageflow.dev` | `Password123!` |

The seed script also creates 5 teams, 4 integrations, 1 active model version, and
10 sample tickets (each run through the ML stub, some pre-assigned to the demo agent).

Log in via:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@triageflow.dev", "password": "Password123!"}'
```
Use the returned `access_token` as `Authorization: Bearer <token>` on subsequent requests.

## Database migrations (Alembic)

- Create a new migration after changing models:
  ```bash
  alembic revision --autogenerate -m "describe your change"
  ```
- Apply migrations:
  ```bash
  alembic upgrade head
  ```
- Roll back one step:
  ```bash
  alembic downgrade -1
  ```

The included `0001_initial_schema.py` creates all 11 tables and matches the
current models exactly (verified with an autogenerate diff during development —
it comes back empty).

## Running tests

Tests run against an **in-memory SQLite database** by default, so you don't need
Postgres running just to test — this keeps the suite fast and dependency-free.
(Set `TEST_DATABASE_URL` to point at a real Postgres instance if you'd rather
test against Postgres directly.)

```bash
cd backend
source .venv/bin/activate   # if not already active
pytest
```

Or with coverage:
```bash
pytest --cov=app --cov-report=term-missing
```

The suite (36 tests) covers:
- **`tests/test_auth.py`** — login success/failure, inactive users, `/auth/me`,
  refresh token flow, invalid/expired tokens
- **`tests/test_roles.py`** — role-based access control across teams, users,
  routing rules, and settings endpoints
- **`tests/test_tickets.py`** — ticket creation (with ML prediction fields),
  search/filter/pagination, assignment, status transitions, message history,
  validation errors
- **`tests/test_feedback.py`** — correct-category, mark-urgency, accept-prediction,
  and their validation rules

## Swapping in a real ML service later

All prediction logic lives behind `app/services/ml_stub.py`'s `BasePredictor`
interface. To connect the real `ml-service/`:

1. Implement a new class (e.g. `RemotePredictor(BasePredictor)`) that calls
   `ml-service` over HTTP/gRPC instead of running the mock heuristic.
2. Point `get_predictor()` at your new class (e.g. behind a settings flag).
3. Nothing else changes — routers, schemas, and the DB shape are already stable.

## Notes for frontend integration

- CORS is pre-configured for `http://localhost:3000` and `http://localhost:5173`
  (edit `CORS_ORIGINS` in `.env` to add more).
- The OpenAPI schema at `/openapi.json` is stable and can be used to generate a
  typed API client for the React app.
- All list endpoints return pagination metadata (`total`, `page`, `page_size`,
  `total_pages`) so the frontend can build pagination controls directly.
