# TideFlow Backend

This folder contains a Django project with a FastAPI gateway mounted on the same ASGI application.

## Layout

- Django serves the core app and root health check.
- FastAPI is mounted under `/api` for gateway-style endpoints.

## Local run

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r backend/requirements.txt
   ```

3. Apply Django migrations:

   ```bash
   cd backend
   python manage.py migrate
   ```

4. Start Django directly:

   ```bash
   cd backend
   python manage.py runserver
   ```

5. Or run the combined ASGI app:

   ```bash
   cd backend
   uvicorn tideflow_backend.asgi:application --reload
   ```

## Docker run

Start the backend in a container with live reload:

```bash
cd backend
docker compose up --build
```

The service will be available at `http://localhost:8000`.

## Endpoints

- `GET /health/` - Django health check
- `GET /api/health` - FastAPI gateway health check
- `POST /api/forward` - gateway scaffold endpoint
