#!/bin/bash
set -e

# Verificar y corregir permisos del directorio de logs
if [ ! -w "/app/logs" ]; then
    echo "⚠️ El directorio de logs no tiene permisos de escritura, intentando corregir..."
    mkdir -p /app/logs
    chmod -R 777 /app/logs
fi

# Iniciar Streamlit
exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.baseUrlPath=/validator