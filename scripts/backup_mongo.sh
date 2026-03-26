#!/usr/bin/env sh
set -eu

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_ROOT=${BACKUP_ROOT:-./backups/mongo}
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"
CONTAINER_NAME=${MONGO_CONTAINER_NAME:-plantas-mongo}
DB_NAME=${MONGO_DB_NAME:-appPlantas}

mkdir -p "$BACKUP_DIR"

echo "Creando backup de MongoDB '${DB_NAME}' en ${BACKUP_DIR}"
docker exec "$CONTAINER_NAME" sh -c "mongodump --db '$DB_NAME' --archive" > "$BACKUP_DIR/${DB_NAME}.archive"

echo "Backup completado: $BACKUP_DIR/${DB_NAME}.archive"
