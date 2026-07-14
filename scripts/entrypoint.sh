#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# entrypoint.sh — Generic entrypoint script for SCONIA backend
# Supports Google Cloud Run, GKE, Render, and local Docker deployments.
# ─────────────────────────────────────────────────────────────────────────────

set -e  # Exit immediately on error

echo "=== SCONIA Production Startup ==="

# ── 1. Derive async DATABASE_URL from sync DATABASE_URL if needed ───────────
if [ -n "$DATABASE_URL" ] && [ -z "$DATABASE_URL_ASYNC" ]; then
    # Convert postgres:// or postgresql:// to postgresql+asyncpg://
    export DATABASE_URL_ASYNC=$(echo "$DATABASE_URL" | sed -E 's/^postgres(ql)?:\/\//postgresql+asyncpg:\/\//')
    echo "[INFO] Derived DATABASE_URL_ASYNC successfully"
fi

# ── 2. Run Database Migrations (Optional) ────────────────────────────────────
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "[INFO] Running Alembic migrations..."
    alembic upgrade head
    echo "[INFO] Migrations completed successfully"
else
    echo "[INFO] Skipping startup migrations (RUN_MIGRATIONS != true)"
fi

# ── 3. Start Uvicorn ──────────────────────────────────────────────────────────
# Default to port 8080 (Cloud Run default) if PORT is not set
TARGET_PORT="${PORT:-8080}"
WORKERS="${WEB_CONCURRENCY:-2}"
LOG_LVL="${LOG_LEVEL:-info}"

echo "[INFO] Starting Uvicorn on port $TARGET_PORT with $WORKERS workers..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$TARGET_PORT" \
    --workers "$WORKERS" \
    --log-level "$LOG_LVL"
