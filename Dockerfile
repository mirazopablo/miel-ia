
# Dockerfile optimizado para Producción con MySQL
FROM python:3.11-slim

#ENV
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY trained_models/ ./trained_models/
COPY alembic/ ./alembic/
COPY alembic.ini ./alembic.ini
COPY start.sh ./start.sh
COPY .env* ./

RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Dar permisos de ejecución al script
RUN chmod +x ./start.sh

CMD ["./start.sh"]