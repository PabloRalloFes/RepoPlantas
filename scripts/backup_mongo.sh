#!/usr/bin/env sh
set -eu

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_ROOT=${BACKUP_ROOT:-./backups/mongo}
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"
CONTAINER_NAME=${MONGO_CONTAINER_NAME:-plantas-mongo}
# Bases usadas por la API (main.py / setup_bbdd.py)
DB_NAMES=${MONGO_DB_NAMES:-"Repositorio_Plantas Usuarios"}
BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-0}

mkdir -p "$BACKUP_DIR"

for DB_NAME in $DB_NAMES; do
  echo "Creando backup de MongoDB '${DB_NAME}' en ${BACKUP_DIR}"
  docker exec "$CONTAINER_NAME" sh -c "mongodump --db '$DB_NAME' --archive" > "$BACKUP_DIR/${DB_NAME}.archive"
  echo "Backup completado: $BACKUP_DIR/${DB_NAME}.archive"
done

if [ "$BACKUP_RETENTION_DAYS" -gt 0 ]; then
  echo "Eliminando copias anteriores a ${BACKUP_RETENTION_DAYS} días en ${BACKUP_ROOT}"
  find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -mtime +"$BACKUP_RETENTION_DAYS" -exec rm -rf {} +
fi

echo "Todos los backups guardados en: $BACKUP_DIR"
