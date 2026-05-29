# DEVELOPMENT — How TideFlow Was Built

This document describes the stages taken to build TideFlow, decisions made, and where to find the implementation for each stage.

## EPIC 1 Project Setup & Auth

## Stage 1 — Project scaffold & ASGI gateway

- Created a Django project as the core app for models, admin, and primary routing.
- Mounted a FastAPI instance under `/api` so we can iterate on API endpoints faster while keeping Django for data and admin.
- Key file: `backend/tideflow_backend/asgi.py` (mounts FastAPI in the ASGI app).

## Stage 2 — Accounts & profiles

- Implemented a user-centered accounts app with flexible profile data.
- `Profile` model holds `role` and `phone` fields and links to Django `User`.
- Ensure `Profile` objects exist for users (created on registration).
- Key file: `backend/accounts/models.py`.

## Stage 3 — JWT auth & session management

- Implemented JWT helper functions to create access and refresh tokens, including `role` in access claims.
- Introduced a `Session` model to persist refresh token `jti`, expiry, user link, and revocation state.
- Middleware (`JWTAuthenticationMiddleware`) reads bearer tokens and sets `request.user` for Django views.
- Key files: `backend/accounts/auth.py`, `backend/accounts/models.py`, `backend/accounts/middleware.py`.

## Stage 4 — Account endpoints

- Implemented `register`, `login`, `refresh`, `logout`, and `set_role` endpoints.
- `set_role` enforces privileges and maps `ADMIN` role to Django `is_staff`/`is_superuser` flags when appropriate.
- Endpoints are registered in `backend/accounts/urls.py` and implemented in `backend/accounts/views.py`.

```bash
cd backend
python manage.py makemigrations accounts
python manage.py migrate
```

- Recommended next work:
  - Add automated tests for the auth flows (register, login, refresh, logout, role enforcement).
  - Prevent the last admin user from being demoted via `set_role`.
  - Add CI steps to run migrations and tests in PRs.

## Notes and references

- Project layout and run instructions: `README.md`
- FastAPI gateway entry: `backend/tideflow_backend/asgi.py`
- Accounts implementation: `backend/accounts/` (models, views, auth, urls, middleware)

If you'd like, I can:

- Run the migrations locally (if you want me to run commands here),
- Add tests for the authentication flows, or
- Create a concise CONTRIBUTING.md for developer onboarding.
