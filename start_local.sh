#!/bin/bash
# Script para iniciar en producción (Modo Tesis)

# 1. Oculta la GPU
export CUDA_VISIBLE_DEVICES=-1

# 2. Silencia TensorFlow (C++)
export TF_CPP_MIN_LOG_LEVEL=2

# Configurar PYTHONPATH
export PYTHONPATH=/app/app

# Iniciar aplicación
# Cambios realizados:
# - workers: Forzado a 1
# - log-level: warning (Oculta los "INFO: Started server...", etc.)
# - no-access-log: (Opcional) Evita que salga una línea por cada petición HTTP (GET /...)

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 1 \
    --reload \
    --log-level info \
    # --no-access-log