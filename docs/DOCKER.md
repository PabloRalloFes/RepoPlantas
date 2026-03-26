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

# URL base para URLs guardadas en BBDD
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
PUBLIC_API_BASE_URL=https://tu-dominio.com
CORS_ORIGINS=https://tu-dominio.com
```

**Para aumentar workers:**
```env
GUNICORN_WORKERS=8
```

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

### Crear Backup
```bash
sh scripts/backup_mongo.sh
# Crea: backups/mongo/<timestamp>/appPlantas.archive
```

### Restaurar Backup
```bash
# Copiar archivo al contenedor
docker cp backups/mongo/<timestamp>/appPlantas.archive plantas-mongo:/tmp/

# Restaurar
docker exec plantas-mongo sh -c \
  "mongorestore --drop --archive=/tmp/appPlantas.archive"
```

---

## 🔐 HTTPS en Producción

### Opción 1: Nginx Reverse Proxy (Recomendado)

```nginx
server {
    listen 443 ssl;
    server_name tu-dominio.com;
    
    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

El contenedor Docker corre en HTTP interno, Nginx termina TLS.

### Opción 2: Flask HTTPS Nativo

Cambiar CMD en Dockerfile:
```dockerfile
CMD ["python", "run_server.py", "--https", "--host", "0.0.0.0", "--port", "5001"]
```

---

## 📋 Checklist de Producción

- [ ] `.env` configurado para dominio real
- [ ] Backup automático programado (cron)
- [ ] HTTPS via Nginx/Reverse Proxy
- [ ] Monitoreo de logs configurado
- [ ] Espacio en disco suficiente
- [ ] MongoDB backup policy clara
- [ ] Health checks configurados

---

