# About TideFlow

TideFlow is a backend service for coordinating passenger flows and deck operations for small ferry or shuttle services. It provides user accounts, role-based access (Passenger, Deck Agent, Admin), and a lightweight API gateway for future mobile and web clients.

Key capabilities:

- User registration and authentication (email/phone + password)
- JWT-based access + refresh token session management
- Role management: `PASSENGER`, `DECK_AGENT`, `ADMIN`
- Admin CRUD for boat routes, schedules, and schedule capacity
- Passenger rides view for date/time/price lookup under `/fleet/rides/`
- Database-backed seat reservations with an optional Redis availability mirror
- Passenger pending bookings under `/fleet/bookings/`
- Paystack checkout for booking payments and webhook confirmation
- FastAPI gateway mounted on top of a Django ASGI app for incremental API development

Tech stack:

- Python 3.x, Django (project core)
- FastAPI (mounted under `/api`) for gateway endpoints
- SQLite by default for local development (configurable)

Quickstart (local):

1. Create a virtual environment and install dependencies:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure the backend environment (PowerShell):

```powershell
$env:DJANGO_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(64))"
$env:DJANGO_DEBUG = "true"
$env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1,[::1]"
$env:REDIS_URL = "redis://127.0.0.1:6379/0"
```

Keep the secret private and reuse it across restarts; changing it invalidates existing JWTs and Django sessions. Django refuses to start without `DJANGO_SECRET_KEY`. Debug is disabled by default. Direct Python commands read process environment variables, not `.env` files. Redis is optional: bookings and availability work from the database during Redis outages. Set `REDIS_URL` to an empty string to disable the mirror locally.

3. Prepare the database and apply migrations:

```bash
python manage.py migrate
```

4. Create a superuser (optional):

```bash
python manage.py createsuperuser
```

5. Run the development server with both Django and the FastAPI gateway:

```bash
uvicorn tideflow_backend.asgi:application --reload
```

For Docker Compose, copy `backend/.env.example` to `backend/.env`, fill in a generated `DJANGO_SECRET_KEY`, and run `docker compose up --build` from `backend`. Compose reads that `.env` file automatically. Add a new Paystack test key when testing checkout; leaving it blank disables payment initialization. The Compose configuration is for local development (source mounts and reload enabled), not production hosting.

Before deployment, set `DJANGO_DEBUG=false`, set `DJANGO_ALLOWED_HOSTS` to the actual hostnames, and configure `APP_BASE_URL` with the public HTTPS URL. Supply secrets through the hosting environment. A previously committed Paystack test key must be revoked and replaced in Paystack; removing it from the current files does not remove it from Git history. Do not reuse that key.

Operation notes:

- The FastAPI gateway is mounted under `/api` by the ASGI app. Health endpoints:
  - `GET /health/` (Django)
  - `GET /api/health` (FastAPI)
- Account endpoints live under the Django app routes. See `backend/accounts/urls.py` for the exact paths (register, login, refresh, logout, set-role).
- Protected API requests accept only access tokens for active users. Refresh tokens are used with the refresh/logout endpoints and cannot authenticate API requests. Refresh requires an unrevoked, unexpired session belonging to the token's user. Inactive users cannot log in or refresh.
- Logout revokes the refresh session. Already issued access tokens remain valid until their 15-minute expiry unless the user is deactivated; immediate per-session access-token revocation is not implemented.
- Fleet admin endpoints live under `backend/fleet/urls.py` and are mounted at `/fleet/`.
- Passenger ride lookup uses `GET /fleet/rides/?date=YYYY-MM-DD&time=HH:MM:SS`.
- Seat availability is capacity minus pending and confirmed booking seats for the specific schedule and ride date. Cancellation releases capacity through the booking's database state. Reservation checks and booking creation share a database transaction, serialized by a write lock on schedule capacity. SQLite lock contention is retried briefly and returns `503` if still busy; insufficient seats return `409`.
- Redis is a best-effort mirror under `tideflow:seat-availability:schedule:<id>:<YYYY-MM-DD>`, refreshed after commits and availability reads with a five-minute TTL. API reads and reservation decisions always use the database, so missing, corrupt, or stale Redis data cannot reopen sold seats. Redis recovery repairs each requested date on its next read; it is not a background rebuild of every key.
- Apply migrations after updating: migration `0006_booking_seat_lookup_index` adds an index for schedule/date/status availability queries. Pending bookings continue to hold seats until cancelled; automatic expiry is Step 6.
- Create a pending booking with `POST /fleet/bookings/` using `schedule_id`, `ride_date`, and optional `seat_count`.
- Initialize payment with `POST /fleet/bookings/<booking_code>/payment/`.
- Cancel an unpaid booking with `DELETE /fleet/bookings/<booking_code>/` using its owner's Bearer access token. Cookie-only authentication is not accepted for cancellation. Paid or confirmed bookings return `409` until a refund workflow is implemented. Repeated cancellation does not release seats again.
- `GET /payment/cancel/` is an informational checkout-return page: it does not cancel bookings or disclose booking details. Failure webhooks cannot cancel bookings already recorded as paid or confirmed. Late payments after cancellation are addressed in subsequent steps.
- Handle Paystack webhooks at `POST /fleet/payments/webhook/`.
- Payment confirmation requires a successful transaction whose reference matches the initialized checkout, whose amount (in minor units) and currency match the booking, and whose metadata contains that booking's code. Both callback verification and signed success webhooks enforce these checks. Repeated confirmations preserve the original payment timestamp; cancelled bookings cannot be confirmed. Initialize checkout before testing confirmation.
- Set `PAYSTACK_SECRET_KEY` and `APP_BASE_URL` in the environment; webhook verification uses the same secret if `PAYSTACK_WEBHOOK_SECRET` is not set.
- Apply migrations before exercising `Profile.role` and `Session` features.

If you want to see how TideFlow was built (design decisions and staged work), see `DEVELOPMENT.md`.
