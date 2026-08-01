
# Dockerfile para Producción Miel-IA (GHCR Image)
FROM python:3.11-slim

# Variables de entorno de entorno de compilación y ejecución de Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    CUDA_VISIBLE_DEVICES=-1 \
    TF_CPP_MIN_LOG_LEVEL=2

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el artefacto de aplicación, modelos de ML y migraciones
COPY app/ ./app/
COPY trained_models/ ./trained_models/
COPY alembic/ ./alembic/
COPY alembic.ini ./alembic.ini
COPY start.sh ./start.sh

# Crear usuario no privilegiado appuser y dar permisos
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app \
    && chmod +x ./start.sh

USER appuser

EXPOSE 8000

CMD ["./start.sh"]