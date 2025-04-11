import os
import requests
import sys
from config import ONTOLOGY_MAPPINGS, ONTOLOGIES_DIR

def download_ontology(url, local_file):
    """Descarga una ontología desde una URL a un archivo local"""
    full_path = os.path.join(ONTOLOGIES_DIR, local_file)
    
    # Saltar si ya existe
    if os.path.exists(full_path):
        print(f"La ontología {local_file} ya existe localmente")
        return True

    print(f"Descargando {url} -> {full_path}")
    try:
        # Intentar varios formatos si la URL original falla
        headers = {'Accept': 'text/turtle, application/rdf+xml, application/ld+json'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        with open(full_path, 'wb') as f:
            f.write(response.content)
            
        print(f"✅ Ontología {local_file} descargada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al descargar {url}: {str(e)}")
        # Intentar alternativas para ciertas URIs conocidas
        if "purl.org" in url:
            alt_url = url.replace("http://purl.org", "https://purl.org")
            try:
                alt_response = requests.get(alt_url, headers=headers, timeout=10)
                alt_response.raise_for_status()
                with open(full_path, 'wb') as f:
                    f.write(alt_response.content)
                print(f"✅ Ontología {local_file} descargada alternativamente desde {alt_url}")
                return True
            except Exception as alt_e:
                print(f"❌ Error con URL alternativa {alt_url}: {str(alt_e)}")
        return False

def main():
    """Descarga todas las ontologías configuradas"""
    # Crear directorio si no existe
    os.makedirs(ONTOLOGIES_DIR, exist_ok=True)
    
    # Descargar cada ontología
    success_count = 0
    failed = []
    
    for url, local_file in ONTOLOGY_MAPPINGS.items():
        if download_ontology(url, local_file):
            success_count += 1
        else:
            failed.append(url)
    
    # Mostrar resumen
    print(f"\nResumen de descarga de ontologías:")
    print(f"✅ {success_count} ontologías descargadas correctamente")
    if failed:
        print(f"❌ {len(failed)} ontologías fallaron:")
        for f in failed:
            print(f"   - {f}")
    else:
        print("Todas las ontologías fueron descargadas correctamente")
    
    return 0 if not failed else 1

if __name__ == "__main__":
    sys.exit(main())