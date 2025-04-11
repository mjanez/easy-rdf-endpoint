#!/bin/bash
set -e

ONTOLOGIES_DIR="/app/ontologies"
LOG_FILE="/app/logs/ontologies-download.log"

# Asegurar que el directorio de logs existe
mkdir -p /app/logs

echo "📥 Iniciando descarga de ontologías para el validador RDF..." | tee -a $LOG_FILE
echo "Fecha: $(date)" | tee -a $LOG_FILE

# Lista completa de ontologías de DCAT-AP-ES con sus URLs
declare -A ONTOLOGIES=(
  # Ontologías principales
  ["dcat2.ttl"]="https://www.w3.org/ns/dcat2.ttl"
  ["dublin_core_terms.ttl"]="http://dublincore.org/2020/01/20/dublin_core_terms.ttl"
  ["foaf.rdf"]="http://xmlns.com/foaf/spec/index.rdf"
  ["locn.ttl"]="https://www.w3.org/ns/locn.ttl"
  ["spdx-ontology.owl.xml"]="https://spdx.org/rdf/terms/spdx-ontology.owl.xml"
  ["schema.org.ttl"]="https://schema.org/version/latest/schemaorg-current-https.ttl"
  ["prov-o.ttl"]="http://www.w3.org/ns/prov-o.ttl"
  ["time.ttl"]="http://www.w3.org/2006/time.ttl"
  ["vcard.ttl"]="http://www.w3.org/2006/vcard/ns.ttl"
  ["adms.ttl"]="http://www.w3.org/ns/adms.ttl"
  
  # URLs alternativas para algunas ontologías (por si fallan las principales)
  ["dc-terms.ttl"]="https://www.dublincore.org/specifications/dublin-core/dcmi-terms/dublin_core_terms.ttl"
  ["skos.rdf"]="https://www.w3.org/2009/08/skos-reference/skos.rdf"
)

# URLs alternativas para ontologías que a veces son problemáticas
declare -A ALTERNATIVE_URLS=(
  ["dcat2.ttl"]="https://raw.githubusercontent.com/SEMICeu/DCAT-AP/master/releases/3.0.0/dcat-ap_3.0.0.ttl"
  ["schema.org.ttl"]="https://schema.org/version/latest/schemaorg-all-https.ttl"
  ["foaf.rdf"]="http://xmlns.com/foaf/spec/20140114.rdf"
  ["prov-o.ttl"]="https://www.w3.org/TR/prov-o/prov-o.ttl"
)

# Contador de éxitos
SUCCESS=0
TOTAL=${#ONTOLOGIES[@]}

download_ontology() {
  local url="$1"
  local dest_file="$2"
  local max_retries="$3"
  local retry=0
  local downloaded=false
  
  while [ $retry -lt $max_retries ] && [ "$downloaded" = false ]; do
    if wget -q --timeout=30 --tries=2 -O "$dest_file" "$url"; then
      # Verificar que el archivo no está vacío y contiene datos válidos
      if [ -s "$dest_file" ] && ! grep -q "<!DOCTYPE html>" "$dest_file"; then
        downloaded=true
        return 0
      else
        echo "⚠️ El archivo descargado está vacío o es HTML en lugar de RDF" | tee -a $LOG_FILE
        rm -f "$dest_file"
      fi
    fi
    
    retry=$((retry+1))
    echo "❌ Intento $retry fallido para $url" | tee -a $LOG_FILE
    
    if [ $retry -lt $max_retries ]; then
      echo "   Reintentando en 3 segundos..." | tee -a $LOG_FILE
      sleep 3
    fi
  done
  
  return 1
}

for ontology_file in "${!ONTOLOGIES[@]}"; do
  url="${ONTOLOGIES[$ontology_file]}"
  dest_file="$ONTOLOGIES_DIR/$ontology_file"
  
  # Si ya existe el archivo, saltarlo
  if [ -f "$dest_file" ] && [ -s "$dest_file" ]; then
    echo "✅ $ontology_file ya existe localmente, saltando..." | tee -a $LOG_FILE
    SUCCESS=$((SUCCESS+1))
    continue
  fi
  
  echo "⬇️ Descargando $ontology_file desde $url..." | tee -a $LOG_FILE
  
  # Intentar descargar la URL principal
  if download_ontology "$url" "$dest_file" 2; then
    echo "✅ Descarga exitosa: $ontology_file" | tee -a $LOG_FILE
    SUCCESS=$((SUCCESS+1))
    continue
  fi
  
  # Si existe una URL alternativa, intentarla
  if [[ -v "ALTERNATIVE_URLS[$ontology_file]" ]]; then
    alt_url="${ALTERNATIVE_URLS[$ontology_file]}"
    echo "🔄 Intentando URL alternativa: $alt_url" | tee -a $LOG_FILE
    
    if download_ontology "$alt_url" "$dest_file" 2; then
      echo "✅ Descarga exitosa con URL alternativa: $ontology_file" | tee -a $LOG_FILE
      SUCCESS=$((SUCCESS+1))
      continue
    fi
  fi
  
  # Si llegamos aquí, la descarga falló con todas las alternativas
  echo "⚠️ No se pudo descargar $ontology_file" | tee -a $LOG_FILE
  
  # Crear un archivo placeholder para no reintentar en cada inicio
  echo "# Error al descargar ontología: $url" > "$dest_file"
  echo "# Fecha: $(date)" >> "$dest_file"
  echo "# Este es un archivo placeholder. La validación SHACL puede fallar para esta ontología." >> "$dest_file"
done

# Mostrar resumen
echo "" | tee -a $LOG_FILE
echo "📊 Resumen de descarga de ontologías:" | tee -a $LOG_FILE
echo "✅ $SUCCESS de $TOTAL ontologías descargadas correctamente" | tee -a $LOG_FILE

if [ $SUCCESS -eq $TOTAL ]; then
  echo "🎉 Todas las ontologías fueron descargadas correctamente" | tee -a $LOG_FILE
  exit 0
else
  echo "⚠️ Algunas ontologías no pudieron descargarse. La validación puede funcionar parcialmente." | tee -a $LOG_FILE
  # No fallamos el script para permitir que el contenedor inicie
  # con funcionalidad parcial si es necesario
  exit 0
fi