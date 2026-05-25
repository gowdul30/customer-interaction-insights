#!/bin/bash
set -e

echo "[STARTUP] Seeding vector database if empty..."
FORCE_SEED=true python scripts/seed_vectordb.py || echo "[WARN] Vector DB seed failed, continuing anyway"

echo "[STARTUP] Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
