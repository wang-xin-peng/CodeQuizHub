#!/bin/bash
"""
CodeQuizHub Database Backup Script
===================================
Usage:
  export DB_PASSWORD="your-password"
  bash scripts/backup_db.sh                    # Manual backup
  bash scripts/backup_db.sh --auto             # Timestamped backup
  bash scripts/backup_db.sh --restore <file>   # Restore from backup

Environment:
  DB_HOST     (default: localhost)
  DB_PORT     (default: 5432)
  DB_NAME     (default: codequizhub)
  DB_USER     (default: codequizhub)
  DB_PASSWORD (required)
  BACKUP_DIR  (default: ./backups)
"""

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-codequizhub}"
DB_USER="${DB_USER:-codequizhub}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"

MODE="${1:-manual}"

mkdir -p "$BACKUP_DIR"

if [ "$MODE" = "--auto" ]; then
    # Automated backup with timestamp
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    FILENAME="codequizhub_${TIMESTAMP}.sql.gz"
    FILEPATH="${BACKUP_DIR}/${FILENAME}"

    echo "[backup] Starting automated backup..."
    echo "[backup] Database: ${DB_NAME} on ${DB_HOST}:${DB_PORT}"

    PGPASSWORD="${DB_PASSWORD}" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --no-owner \
        --no-acl \
        --format=custom \
        --compress=9 \
        --file="${FILEPATH}.dump"

    echo "[backup] Backup saved to: ${FILEPATH}.dump"
    echo "[backup] Size: $(du -h "${FILEPATH}.dump" | cut -f1)"

    # Retention: keep last 30 daily backups, remove older ones
    find "$BACKUP_DIR" -name "codequizhub_*.dump" -mtime +30 -delete
    echo "[backup] Retention: removed backups older than 30 days"

elif [ "$MODE" = "--restore" ]; then
    RESTORE_FILE="$2"
    if [ -z "$RESTORE_FILE" ]; then
        echo "[backup] Error: no restore file specified"
        echo "Usage: bash scripts/backup_db.sh --restore <backup_file.dump>"
        exit 1
    fi
    if [ ! -f "$RESTORE_FILE" ]; then
        echo "[backup] Error: file not found: $RESTORE_FILE"
        exit 1
    fi

    echo "[backup] Restoring database from: $RESTORE_FILE"
    echo "[backup] WARNING: This will OVERWRITE the current database!"

    # Drop existing connections and restore
    PGPASSWORD="${DB_PASSWORD}" psql \
        -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '$DB_NAME'
              AND pid <> pg_backend_pid();"

    PGPASSWORD="${DB_PASSWORD}" pg_restore \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --clean \
        --no-owner \
        --no-acl \
        "$RESTORE_FILE"

    echo "[backup] Restore complete!"
else
    # Manual single-file SQL backup
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    FILENAME="codequizhub_manual_${TIMESTAMP}.sql"
    FILEPATH="${BACKUP_DIR}/${FILENAME}"

    echo "[backup] Starting manual backup..."
    echo "[backup] Database: ${DB_NAME} on ${DB_HOST}:${DB_PORT}"

    PGPASSWORD="${DB_PASSWORD}" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --no-owner \
        --no-acl \
        --clean \
        --if-exists \
        --file="$FILEPATH"

    gzip -f "$FILEPATH"
    echo "[backup] Backup saved to: ${FILEPATH}.gz"
    echo "[backup] Size: $(du -h "${FILEPATH}.gz" | cut -f1)"
fi
