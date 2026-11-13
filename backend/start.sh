#!/bin/bash
set -e

echo "=== Medicall Production Backend Startup ==="

echo "Step 1: Running database migrations..."
alembic upgrade head

echo "Step 2: Checking database seed status..."
python -m app.db.seed || echo "Seed check completed or already populated."

echo "Step 3: Launching Uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers
