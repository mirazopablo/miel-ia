#!/bin/bash

# Disable GPU and suppress TensorFlow C++ logs to prevent C-extension crashes on CPU-only hosts
export CUDA_VISIBLE_DEVICES=-1
export TF_CPP_MIN_LOG_LEVEL=2

echo "🚀 Iniciando Miel-IA Backend API..."

# Verificar conexión a PostgreSQL
max_retries=30
count=0

echo "🔍 Verificando disponibilidad de base de datos PostgreSQL..."

# Loop de espera hasta que la base de datos responda
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
    print('✅ Base de datos PostgreSQL lista!')
    sys.exit(0)
except Exception as e:
    print(f'⏳ Esperando a la base de datos PostgreSQL... ({e})')
    sys.exit(1)
"
    if [ $? -eq 0 ]; then
        break
    fi
    
    count=$((count+1))
    echo "Reintentando en 2 segundos... ($count/$max_retries)"
    sleep 2
done

if [ $count -eq $max_retries ]; then
    echo "❌ Error: No se pudo conectar a la base de datos PostgreSQL después de $max_retries intentos."
    exit 1
fi

echo "🔍 Validando importación y estructura de la aplicación FastAPI..."
python3 -c "
import sys
import os
sys.path.append('/app')
try:
    import app.main
    print('✅ Importación de app.main exitosa!')
except Exception as e:
    import traceback
    print('❌ Error al cargar app.main:')
    traceback.print_exc()
    sys.exit(1)
"
if [ $? -ne 0 ]; then
    echo "❌ Error crítico al cargar la aplicación FastAPI. Abortando."
    exit 1
fi

# Iniciar la aplicación FastAPI con Uvicorn
echo "🌟 Iniciando servidor FastAPI con Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1