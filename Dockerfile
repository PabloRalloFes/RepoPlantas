FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias de sistema para OpenCV/PIL y utilidades basicas.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --extra-index-url https://download.pytorch.org/whl/cpu/torch_stable.html \
        torch==2.9.0 torchvision==0.24.0 \
    && pip install -r requirements.txt

COPY . .

EXPOSE 5001

# En despliegue real, TLS debe terminar en reverse proxy (Nginx/Caddy) y la API
# correr en HTTP interno mediante Gunicorn.
CMD ["sh", "-c", "gunicorn --workers ${GUNICORN_WORKERS:-2} --timeout ${GUNICORN_TIMEOUT:-120} --bind 0.0.0.0:5001 main:app"]
