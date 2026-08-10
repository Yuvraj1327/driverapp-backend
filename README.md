# FleetFlow — Fleet Management & Driver Expense System

A production-ready **FastAPI** backend for managing a vehicle fleet: drivers, vehicle
assignments, daily KM logs, driver expenses with a receipt-upload + approval workflow,
tyre and service-history tracking, automatic reminders (insurance/registration expiry),
in-app notifications, and daily/weekly/monthly/vehicle/driver/expense reports exportable
to PDF and Excel.

---

## Tech Stack

| Layer            | Technology                                   |
|-------------------|-----------------------------------------------|
| Framework          | FastAPI (async)                               |
| Database           | PostgreSQL (Supabase-compatible)              |
| ORM                | SQLAlchemy 2.0 (async, `asyncpg`)              |
| Migrations         | Alembic                                       |
| Validation         | Pydantic v2                                   |
| Auth               | JWT (access + refresh) via `python-jose`       |
| Passwords          | `bcrypt` (direct, no passlib)                  |
| Scheduler          | APScheduler (reminder & expiry checks)         |
| File storage       | Supabase Storage (falls back to local disk)    |
| Reports            | Pandas + OpenPyXL (Excel), ReportLab (PDF)     |
| Server             | Uvicorn                                       |
| Containerization   | Docker / Docker Compose                        |

---

## Architecture

Clean, layered architecture — each layer only talks to the one below it:

```
API routers (app/api/v1)      → HTTP concerns, dependency injection, response shaping
    ↓
Services (app/services)       → business rules, transactions, orchestration
    ↓
Repositories (app/repositories) → query construction, persistence
    ↓
Models (app/models)           → SQLAlchemy ORM schema
```

Cross-cutting layers:
- `app/core` — settings, JWT/password utilities, enums/constants, logging config
- `app/auth` — JWT parsing + FastAPI dependencies for role-based access control
- `app/schemas` — Pydantic request/response contracts (never leak ORM models to clients)
- `app/middleware` — request logging + centralized exception → HTTP mapping
- `app/utils` — receipt storage, PDF/Excel export helpers
- `app/jobs` — APScheduler background jobs

```
backend/
├── app/
│   ├── api/v1/          # Routers: auth, users, drivers, vehicles, assignments,
│   │                    #   km_logs, expenses, expense_categories, tyres,
│   │                    #   services, reminders, notifications, reports
│   ├── core/            # config.py, security.py, constants.py, logging_config.py
│   ├── database/        # base.py (Base + mixins), session.py (async engine)
│   ├── models/           # 15 SQLAlchemy models (see below)
│   ├── schemas/          # Pydantic Create/Update/Read schemas
│   ├── repositories/      # Generic + entity-specific data access
│   ├── services/          # Business logic + domain exceptions
│   ├── auth/             # JWT handler + get_current_user / RoleChecker deps
│   ├── middleware/        # Logging middleware + global exception handlers
│   ├── utils/             # storage.py, pdf_export.py, excel_export.py
│   ├── jobs/              # scheduler.py (APScheduler reminder jobs)
│   ├── seed.py            # Dummy-data seed script
│   └── main.py            # FastAPI app entrypoint
├── alembic/               # Migrations (async env.py + initial schema)
├── tests/                 # Pytest suite (SQLite in-memory, no external services needed)
├── uploads/                # Local fallback storage for receipts + generated reports
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Database Schema

| Table                 | Purpose                                                          |
|------------------------|-------------------------------------------------------------------|
| `roles`                | admin / manager / driver                                         |
| `users`                | Login accounts (email + hashed password + role)                  |
| `drivers`              | Driver profile linked 1:1 to a `users` row                        |
| `vehicles`             | Fleet vehicles, odometer, insurance/mulkiya (registration) expiry |
| `vehicle_assignments`  | Driver ↔ vehicle assignment history (one active at a time each)  |
| `km_logs`              | Daily start/end odometer entries → auto distance calculation      |
| `expense_categories`   | Fuel, Toll, Parking, Maintenance, Fines, Car Wash, ...             |
| `expenses`             | Driver expenses, optional receipt URL, approval status            |
| `expense_approvals`    | Audit trail of who approved/rejected each expense and why          |
| `tyres`                | Tyre install/removal, expected life, position, cost                |
| `services`             | Maintenance/service history, next-due km/date                     |
| `reminders`            | Insurance/mulkiya expiry, service due, tyre change, custom          |
| `notifications`        | Per-user in-app notifications (approvals, reminders, etc.)         |
| `reports`              | Persisted record of every generated PDF/Excel export                |

All tables have `id` (UUID PK), `created_at`, `updated_at` audit columns.

---

## Roles & Permissions

| Action                                   | Admin | Manager | Driver |
|--------------------------------------------|:-----:|:-------:|:------:|
| Manage users                               |  ✅   |    ❌   |   ❌   |
| Create/update drivers & vehicles            |  ✅   |    ✅   |   ❌   |
| Delete drivers/vehicles                     |  ✅   |    ❌   |   ❌   |
| Assign/unassign vehicles                    |  ✅   |    ✅   |   ❌   |
| Log KM / submit expenses                    |  ✅   |    ✅   |   ✅   |
| Approve/reject expenses                     |  ✅   |    ✅   |   ❌   |
| View dashboard/reports                      |  ✅   |    ✅   |   ✅   |
| Export reports (PDF/Excel)                  |  ✅   |    ✅   |   ❌   |

---

## Getting Started

### Option A — Docker Compose (recommended)

```bash
cd backend
cp .env.example .env          # edit SECRET_KEY, Supabase creds, etc.
docker compose up --build
```

This starts a local Postgres container **and** the API, running `alembic upgrade head`
automatically before boot. Once healthy:

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Seed dummy data (run once, inside the running `api` container):

```bash
docker compose exec api python -m app.seed
```

### Option B — Local Python environment

Requires Python 3.13+ and a running PostgreSQL instance (or a Supabase project).

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: DATABASE_URL, SYNC_DATABASE_URL, SECRET_KEY, SUPABASE_* (optional)

alembic upgrade head
python -m app.seed                # optional: populate demo data

uvicorn app.main:app --reload
```

---

## Demo Credentials (after seeding)

| Role    | Email                    | Password     |
|---------|---------------------------|---------------|
| Admin   | admin@fleetflow.com        | Admin@123     |
| Manager | manager@fleetflow.com      | Manager@123   |
| Driver  | driver1@fleetflow.com      | Driver@123    |

---

## Environment Variables

See `.env.example` for the full list. Key ones:

| Variable                        | Description                                                   |
|-----------------------------------|-----------------------------------------------------------------|
| `DATABASE_URL`                    | Async SQLAlchemy URL (`postgresql+asyncpg://...`) — app runtime |
| `SYNC_DATABASE_URL`               | Sync URL (`postgresql+psycopg2://...`) — used by some tooling   |
| `SECRET_KEY`                      | JWT signing secret — **change in production**                   |
| `ACCESS_TOKEN_EXPIRE_MINUTES`     | Access token lifetime (default 30)                               |
| `REFRESH_TOKEN_EXPIRE_DAYS`       | Refresh token lifetime (default 7)                               |
| `SUPABASE_URL` / `SUPABASE_KEY`   | Enables Supabase Storage for receipt uploads (optional)          |
| `SUPABASE_STORAGE_BUCKET`         | Bucket name for receipts (default `receipts`)                    |
| `UPLOAD_DIR`                      | Local fallback storage path when Supabase isn't configured        |
| `REMINDER_CHECK_INTERVAL_HOURS`   | How often APScheduler re-scans for expiring documents             |
| `DOCUMENT_EXPIRY_ALERT_DAYS`      | How many days ahead of expiry to raise a reminder                 |

> If `SUPABASE_URL`/`SUPABASE_KEY` are left blank, receipt uploads and report files are
> stored on local disk under `uploads/` and served via the app's static file mount —
> the app is fully functional without a Supabase project.

---

## API Overview

All endpoints are namespaced under `/api/v1`. Full interactive documentation (with
request/response schemas and the ability to try requests) is at **`/docs`**.

| Group                | Endpoints (abridged) |
|------------------------|----------------------|
| Auth                   | `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me` |
| Users                  | `POST/GET /users`, `GET/PUT/DELETE /users/{id}`, `POST /users/me/change-password` |
| Drivers                | `POST/GET /drivers`, `GET/PUT/DELETE /drivers/{id}` |
| Vehicles               | `POST/GET /vehicles`, `GET/PUT/DELETE /vehicles/{id}` |
| Vehicle Assignments    | `POST /assignments`, `POST /assignments/{id}/unassign`, `GET /assignments` |
| KM Logs                | `POST /km-logs`, `PUT/GET /km-logs/{id}`, `GET /km-logs/vehicle/{id}/history`, `GET /km-logs/driver/{id}/history` |
| Expense Categories     | `POST/GET /expense-categories`, `PUT/DELETE /expense-categories/{id}` |
| Expenses               | `POST/GET /expenses`, `GET/PUT/DELETE /expenses/{id}`, `POST /expenses/{id}/receipt`, `POST /expenses/{id}/review` |
| Tyres                  | `POST/GET /tyres`, `GET/PUT/DELETE /tyres/{id}` |
| Service History        | `POST/GET /services`, `GET/PUT/DELETE /services/{id}` |
| Reminders              | `POST/GET /reminders`, `PUT /reminders/{id}`, `POST /reminders/{id}/mark-read` |
| Notifications          | `GET /notifications`, `POST /notifications/{id}/mark-read` |
| Reports                | `GET /reports/dashboard`, `/daily`, `/weekly`, `/monthly`, `/vehicle-wise`, `/driver-wise`, `/expense-wise`, `POST /reports/export`, `GET /reports/export/{id}/download` |

All list endpoints support `page` and `page_size` query params and return a
`{items, total, page, page_size, pages}` envelope.

---

## Business Rules Worth Knowing

- **KM logs auto-calculate distance** (`end_odometer - start_odometer`) and push the
  vehicle's `current_odometer` forward; a new log's `start_odometer` cannot be less
  than the vehicle's last recorded odometer.
- **One active assignment at a time**: a vehicle can't be assigned to two drivers
  simultaneously, and a driver can't be assigned to two vehicles simultaneously.
  Assigning marks the driver unavailable; unassigning frees them up again.
- **Expense approval workflow**: expenses are created as `pending`; only a
  manager/admin can `approve`/`reject` via `POST /expenses/{id}/review`, which is
  recorded in `expense_approvals` and notifies the submitting driver. Only `pending`
  expenses can still be edited by their owner.
- **Reminders & notifications**: a background APScheduler job periodically scans
  vehicles for insurance/mulkiya expiry within `DOCUMENT_EXPIRY_ALERT_DAYS` and creates
  `reminders`; a second job turns due reminders into `notifications` for admins/managers.
- **Reports**: `daily`/`weekly`/`monthly` reports default to the current period if no
  explicit start/end dates are given. `vehicle-wise`, `driver-wise`, and `expense-wise`
  reports require an explicit date range. `POST /reports/export` persists a `Report`
  row and writes a PDF or Excel file under `uploads/reports/`, downloadable via
  `GET /reports/export/{id}/download`.

---

## Running Tests

The test suite runs against an **in-memory SQLite database** via `aiosqlite` — no
Postgres or Supabase project required.

```bash
pip install -r requirements.txt
pytest -v
```

Covers: login/refresh/me, vehicle CRUD + conflict handling, driver creation
(auto-provisions a linked user), KM log distance auto-calculation and validation,
the full expense approval lifecycle, the dashboard summary, and PDF/Excel report
export.

---

## Database Migrations

```bash
# Apply all migrations
alembic upgrade head

# Create a new migration after changing models
alembic revision --autogenerate -m "add new_field to vehicles"

# Roll back one revision
alembic downgrade -1
```

---

## Production Notes

- Set a strong, random `SECRET_KEY` and short `ACCESS_TOKEN_EXPIRE_MINUTES` in production.
- Put the API behind a reverse proxy (nginx/Caddy) terminating TLS; Uvicorn itself
  is run without TLS in the provided Dockerfile.
- Logs are written both to stdout (for container log aggregation) and to a rotating
  file under `logs/fleetflow.log`.
- The `/health` endpoint is wired for container orchestrator liveness/readiness probes.
- Configure `SUPABASE_URL`/`SUPABASE_KEY` for durable, CDN-backed receipt storage
  instead of the local-disk fallback.

---

## License

Provided as-is for internal fleet management use.
