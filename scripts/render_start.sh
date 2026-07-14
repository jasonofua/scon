#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# render_start.sh — Startup script for SCONIA backend on Render
#
# Responsibilities:
#   1. Convert the sync DATABASE_URL to async (asyncpg) if not already set
#   2. Run Alembic migrations
#   3. Start the Uvicorn server
# ─────────────────────────────────────────────────────────────────────────────

set -e  # Exit immediately on error

echo "=== SCONIA Render Startup ==="

# ── 1. Derive async DATABASE_URL from sync one if not explicitly set ─────────
if [ -z "$DATABASE_URL_ASYNC" ] && [ -n "$DATABASE_URL" ]; then
    export DATABASE_URL_ASYNC="${DATABASE_URL/postgresql:\/\//postgresql+asyncpg://}"
    export DATABASE_URL_ASYNC="${DATABASE_URL_ASYNC/postgres:\/\//postgresql+asyncpg://}"
    echo "[INFO] DATABASE_URL_ASYNC derived from DATABASE_URL"
fi

echo "[INFO] DATABASE_URL_ASYNC = ${DATABASE_URL_ASYNC//:*@/:***@}"  # mask password

# ── 2. Create required directories ───────────────────────────────────────────
mkdir -p /app/uploads /app/data /app/logs /app/tiktoken_cache
echo "[INFO] Directories created"

# ── 3. Run database migrations ───────────────────────────────────────────────
echo "[INFO] Running Alembic migrations..."
alembic upgrade head
echo "[INFO] Migrations complete"

# ── 4. Start the application ─────────────────────────────────────────────────
echo "[INFO] Starting Uvicorn..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --log-level "${LOG_LEVEL:-info}"
