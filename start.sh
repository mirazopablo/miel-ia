#!/bin/bash

echo "🚀 Iniciando Miel-IA..."

# Verificar conexión a MySQL
max_retries=30
count=0

echo "🔍 Verificando disponibilidad de base de datos..."

# Loop de espera hasta que la base de datos responda
# Usamos un pequeño script de python para intentar conectar
while [ $count -lt $max_retries ]; do
    python3 -c "
import sys
import os
from sqlalchemy import create_engine, text
sys.path.append('/app')
try:
    from app.core.config import settings
    db_uri = settings.DATABASE_URL
    
    engine = create_engine(db_uri)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ Base de datos lista!')
    sys.exit(0)
except Exception as e:
    print(f'⏳ Esperando a base de datos... ({e})')
    sys.exit(1)
"
    if [ $? -eq 0 ]; then
        break
    fi
    
    count=$((count+1))
    echo "Retrying in 2 seconds... ($count/$max_retries)"
    sleep 2
done

if [ $count -eq $max_retries ]; then
    echo "❌ Error: No se pudo conectar a la base de datos después de $max_retries intentos."
    exit 1
fi

# Migraciones (si aplica)
# echo "Running migrations..."
# alembic upgrade head

# Iniciar la aplicación
echo "🌟 Iniciando servidor FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1