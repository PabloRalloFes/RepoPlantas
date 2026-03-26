# Docker del Servidor + MongoDB (Guia Rapida)

Esta guia levanta **todo el backend** en contenedores:
- API Flask (`main.py` via `run_server.py`)
- MongoDB persistente

## 1) Requisitos
- Docker Desktop (Windows/Mac) o Docker Engine + Compose (Linux)
- Git

Comprobar:
```bash
docker --version
docker compose version
```

## 2) Primer arranque desde cero
Desde la raiz del repo:

```bash
# 1) (Opcional) Crear archivo .env propio a partir de la plantilla
cp .env.docker.example .env

# 2) Construir imagen de la API
docker compose build

# 3) Levantar API + MongoDB
docker compose up -d mongo api

# 4) Ver logs (dejar corriendo para comprobar arranque)
docker compose logs -f api
```

La API quedara accesible en:
- `http://localhost:5001`

MongoDB quedara accesible en:
- `mongodb://localhost:27017`

## 3) Inicializar BBDD base (colecciones/etiquetas)
Para inicializar la base de datos en una maquina limpia ejecuta como servicio one-shot

```bash
docker compose --profile init run --rm initdb
```

## 4) Persistencia de datos
- Mongo guarda datos en volumen `mongo_data`.
- La API monta carpetas del repo para persistir artefactos:
  - `imagenes/`
  - `logs/`
  - `models/`
  - `experiments/`
  - `data/`
  - `ssl_certs/`

Si borras contenedores, los datos de Mongo siguen mientras no elimines el volumen.

## 5) Comandos de operacion diaria
```bash
# Levantar
docker compose up -d

# Parar
docker compose down

# Ver estado
docker compose ps

# Ver logs API
docker compose logs -f api

# Reiniciar solo API
docker compose restart api
```

## 6) Integracion con app movil/desktop
Para que la app cliente se conecte al backend Docker en la misma maquina:
- URL API: `http://localhost:5001`

Si la app corre en otro dispositivo de la red (misma LAN):
- URL API: `http://IP_DE_TU_SERVIDOR:5001`

## 7) HTTPS
En Docker Compose actual, la API corre en **HTTP interno** para simplificar despliegue local.
Para dejarlo en condiciones de producción:
- dejar API interna en HTTP
- poner un proxy inverso (nginx/caddy/traefik) con HTTPS delante


## 8) Problemas comunes
- Build muy pesado: `torch` y `torchvision` pesan bastante.
- Puerto ocupado: cambia mapeo en `docker-compose.yml` (por ejemplo `5002:5001`).
- API no arranca: revisar `docker compose logs -f api`.
- Init falla: asegurate de que `api` esta healthy antes de lanzar `initdb`.

## 9) Prueba completa de reproducibilidad (checklist)
1. Clonar repo en otra maquina.
2. `docker compose build`.
3. `docker compose up -d mongo api`.
4. `docker compose --profile init run --rm initdb`.
5. Probar endpoint: abrir `http://localhost:5001/opciones_modelos`.
6. Subir una imagen desde app/script y confirmar insercion en Mongo.

