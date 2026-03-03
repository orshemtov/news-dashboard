#!/bin/sh
set -e

echo "Running database migrations..."
/app/.venv/bin/alembic upgrade head

echo "Starting server..."
exec /app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
