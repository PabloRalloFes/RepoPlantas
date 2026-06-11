# 🐳 Guía de Docker - Despliegue en Servidor

**Para DevOps/Administradores que quieren desplegar en un servidor.**

---

## 📋 Requisitos

- Docker Desktop (Windows/Mac) o Docker Engine (Linux)
- Docker Compose
- Git

Verificar:
```bash
docker --version
docker compose version
```

---

## 🚀 Primer Arranque (3 Pasos)

### 1. Clonar Repositorio
```bash
git clone https://github.com/PabloRalloFes/RepoPlantas.git
cd RepoPlantas
```

### 2. Crear Archivo de Configuración
```bash
cp .env.docker.example .env
# Edita .env con tus valores reales si es necesario
```

### 3. Levantar Stack Completo
```bash
# Construir imagen
docker compose build

# Arrancar servicios
docker compose up -d

# Verificar estado
docker compose ps
```

La API estará accesible en: **`http://localhost:5001`**

La raíz del dominio o del servidor puede servir una landing pública con enlaces de descarga y texto de uso. Los enlaces pueden apuntar a endpoints tipo `/download/windows`, `/download/linux` y `/download/android`, que devuelven directamente los ZIP almacenados en la máquina virtual.

---

## 📊 Servicios

El `docker-compose.yml` levanta:

| Servicio | Imagen | Puerto | Función |
|----------|--------|--------|---------|
| `mongo` | mongo:7 | 27017 | Base de datos NoSQL |
| `api` | Custom (Dockerfile) | 5001 | API Flask + Gunicorn |
| `initdb` | Custom (Dockerfile) | - | Inicializa BBDD (one-shot) |

---

## ⚙️ Configuración

### Variables de Entorno (.env)

```env
# Conexión interna (Docker)
URL_BBDD=mongodb://mongo:27017/

# URL que usan scripts internos de Docker
URL_API=http://api:5001

# URL base para URLs guardadas en BBDD (local)
PUBLIC_API_BASE_URL=http://127.0.0.1:5001

# Gunicorn workers
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=120

# Máximo tamaño imagen (MB)
MAX_IMAGE_SIZE_MB=10
```

### Cambios Habituales

**Para producción remota:**
```env
PUBLIC_API_BASE_URL=https://plantas.gti-ia.upv.es
```

**Para aumentar workers:**
```env
GUNICORN_WORKERS=8
```

**Para publicar las descargas de la app desde la VM:**
```env
DOWNLOADS_DIR=/ruta/local/a/downloads
DOWNLOAD_WINDOWS_FILE=Foliarium-Windows.zip
DOWNLOAD_LINUX_FILE=Foliarium-Linux.zip
DOWNLOAD_ANDROID_FILE=Foliarium-Android.zip
```

Coloca esos ZIP en la ruta indicada y la landing los servirá como descargas directas.

---

## 📈 Operaciones Diarias

### Ver logs
```bash
docker compose logs -f api
docker compose logs -f mongo
```

### Reiniciar servicio
```bash
docker compose restart api
```

### Parar todo
```bash
docker compose down
```

### Parar pero guardar volúmenes
```bash
docker compose down --volumes
```

---

## 💾 Backup y Restore

Foliarium usa dos bases en MongoDB: `Repositorio_Plantas` (datos) y `Usuarios` (credenciales).
El script `scripts/backup_mongo.sh` vuelca ambas.

### Crear backup manual

Desde el directorio del proyecto, con el stack levantado:

```bash
sh scripts/backup_mongo.sh
# Crea: backups/mongo/<timestamp>/Repositorio_Plantas.archive
#       backups/mongo/<timestamp>/Usuarios.archive
```

Variables opcionales:

```bash
BACKUP_ROOT=/var/backups/foliarium/mongo \
MONGO_CONTAINER_NAME=plantas-mongo \
BACKUP_RETENTION_DAYS=30 \
sh scripts/backup_mongo.sh
```

- `BACKUP_ROOT`: carpeta destino (en producción conviene una ruta fuera del repo).
- `BACKUP_RETENTION_DAYS`: si es > 0, borra subcarpetas más antiguas.

### Backup automático (cron en la VM)

En el servidor universitario, programa una copia periódica **en el host** (no dentro del contenedor):

```bash
crontab -e
```

Ejemplo semanal (domingos a las 03:00):

```cron
0 3 * * 0 cd /ruta/al/RepoPlantas && BACKUP_ROOT=/var/backups/foliarium/mongo BACKUP_RETENTION_DAYS=30 sh scripts/backup_mongo.sh >> /var/log/foliarium-backup.log 2>&1
```

Ejecuta también un backup manual **antes** de importaciones masivas o cambios de esquema.

### Restaurar backup

```bash
# Copiar archivo al contenedor
docker cp backups/mongo/<timestamp>/Repositorio_Plantas.archive plantas-mongo:/tmp/
docker cp backups/mongo/<timestamp>/Usuarios.archive plantas-mongo:/tmp/

# Restaurar (repetir por cada base)
docker exec plantas-mongo sh -c \
  "mongorestore --drop --db Repositorio_Plantas --archive=/tmp/Repositorio_Plantas.archive"
docker exec plantas-mongo sh -c \
  "mongorestore --drop --db Usuarios --archive=/tmp/Usuarios.archive"
```

---


## 📋 Checklist de Producción

- [ ] `.env` configurado para dominio real
- [ ] Backup automático programado (cron)
- [ ] Monitoreo de logs configurado
- [ ] Espacio en disco suficiente
- [ ] MongoDB backup policy clara
- [ ] Health checks configurados

---

