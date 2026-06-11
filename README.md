## About TideFlow

TideFlow is a backend service for coordinating passenger flows and deck operations for small ferry or shuttle services. It provides user accounts, role-based access (Passenger, Deck Agent, Admin), and a lightweight API gateway for future mobile and web clients.

Key capabilities:

- User registration and authentication (email/phone + password)
- JWT-based access + refresh token session management
- Role management: `PASSENGER`, `DECK_AGENT`, `ADMIN`
- Admin CRUD for boat routes, schedules, and schedule capacity
- Passenger rides view for date/time/price lookup under `/fleet/rides/`
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

2. Prepare the database and apply migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

3. Create a superuser (optional):

```bash
python manage.py createsuperuser
```

4. Run the development server:

```bash
python manage.py runserver
```

Operation notes:

- The FastAPI gateway is mounted under `/api` by the ASGI app. Health endpoints:
  - `GET /health/` (Django)
  - `GET /api/health` (FastAPI)
- Account endpoints live under the Django app routes. See `backend/accounts/urls.py` for the exact paths (register, login, refresh, logout, set-role).
- Fleet admin endpoints live under `backend/fleet/urls.py` and are mounted at `/fleet/`.
- Passenger ride lookup uses `GET /fleet/rides/?date=YYYY-MM-DD&time=HH:MM:SS`.
- Apply migrations before exercising `Profile.role` and `Session` features.

If you want to see how TideFlow was built (design decisions and staged work), see `DEVELOPMENT.md`.
