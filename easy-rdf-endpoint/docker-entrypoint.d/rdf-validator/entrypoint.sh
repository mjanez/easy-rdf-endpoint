#!/bin/bash
set -e

echo "🔄 Iniciando RDF Validator..."

# Verificar estructura de directorios
mkdir -p /app/logs /app/data /app/temp /app/ontologies

# Ejecutar primero la descarga de ontologías
echo "🔍 Descargando ontologías necesarias..."
/app/download-ontologies.sh

# Mostrar información sobre el entorno
echo "🏁 Entorno preparado, iniciando aplicación..."
echo "- Ontologías en: /app/ontologies"
echo "- Logs en: /app/logs"
echo "- Archivos temporales en: /app/temp"

# Ejecutar el comando que se pasa como argumento (CMD del Dockerfile)
echo "🚀 Iniciando aplicación principal..."
exec "$@"