#!/bin/sh
# docker-entrypoint.sh
#
# Idempotent startup script that:
#   1. Runs database migrations (safe to run multiple times)
#   2. Passes through to CMD
#
# Usage: docker-entrypoint.sh [command...]

set -e

echo "[entrypoint] Running database migrations..."
alembic upgrade head
echo "[entrypoint] Migrations up to date."

echo "[entrypoint] Starting application: $@"
exec "$@"
