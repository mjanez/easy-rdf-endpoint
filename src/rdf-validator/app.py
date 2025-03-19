import os
import subprocess
import streamlit as st
import time
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="RDF/XML Validator",
    page_icon="✅",
    layout="wide"
)

st.title("RDF Validator")
st.write("Valida archivos RDF utilizando [Apache Jena RIOT](https://jena.apache.org/documentation/io/).")

# Directorio de datos
DATA_DIR = "/app/data"
LOGS_DIR = "/app/logs"

# Asegurar que exista el directorio de logs
os.makedirs(LOGS_DIR, exist_ok=True)

# Función para listar archivos RDF
def list_rdf_files():
    if not os.path.exists(DATA_DIR):
        return []
    return [f for f in os.listdir(DATA_DIR) if f.endswith(('.rdf', '.xml', '.ttl', '.n3', '.nt', '.jsonld'))]

# Función para validar RDF
def validate_rdf(file_path, base_uri, syntax):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{LOGS_DIR}/validation_{timestamp}.log"
    
    # Construir comando riot
    cmd = [
        "riot", 
        "--validate",
        "--check",
        "--strict",
        "--verbose",
        f"--syntax={syntax}",
        f"--base={base_uri}",
        "--time",
        file_path,
    ]
    
    try:
        # Ejecutar comando y capturar salida
        validation_result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Guardar log
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"COMMAND: {' '.join(cmd)}\n")
            f.write(f"STDOUT:\n{validation_result.stdout}\n")
            f.write(f"STDERR:\n{validation_result.stderr}\n")
            f.write(f"EXIT CODE: {validation_result.returncode}\n")
        
        return {
            "success": validation_result.returncode == 0,
            "stdout": validation_result.stdout,
            "stderr": validation_result.stderr,
            "log_file": log_file
        }
    except subprocess.CalledProcessError as e:
        error_msg = f"Error executing command: {str(e)}"
        # Guardar log de error
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"COMMAND: {' '.join(cmd)}\n")
            f.write(f"ERROR: {error_msg}\n")
            f.write(f"STDOUT:\n{e.stdout}\n")
            f.write(f"STDERR:\n{e.stderr}\n")
        
        return {
            "success": False,
            "stderr": error_msg,
            "log_file": log_file
        }
    except FileNotFoundError as e:
        error_msg = f"Command not found: {str(e)}"
        # Guardar log de error
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"COMMAND: {' '.join(cmd)}\n")
            f.write(f"ERROR: {error_msg}\n")
        
        return {
            "success": False,
            "stderr": error_msg,
            "log_file": log_file
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        # Guardar log de error
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"COMMAND: {' '.join(cmd)}\n")
            f.write(f"ERROR: {error_msg}\n")
        
        return {
            "success": False,
            "stderr": error_msg,
            "log_file": log_file
        }

# UI principal
st.sidebar.header("Opciones de Validación")

# Lista de archivos RDF disponibles
files = list_rdf_files()
if not files:
    st.warning("No se encontraron archivos RDF en el directorio de datos.")
else:
    selected_file = st.sidebar.selectbox("Seleccionar archivo RDF", files)
    file_path = os.path.join(DATA_DIR, selected_file)
    
    # Opciones de validación
    base_uri = st.sidebar.text_input("Base URI", value="http://datos.gob.es/catalogo")
    syntax_options = ["RDF/XML", "Turtle", "N-Triples", "TriG", "N-Quads", "JSON-LD"]
    syntax = st.sidebar.selectbox("Formato de sintaxis", syntax_options)
    
    # Botón para ejecutar validación
    if st.sidebar.button("Validar RDF"):
        with st.spinner('Validando archivo RDF...'):
            start_time = time.time()
            result = validate_rdf(file_path, base_uri, syntax)
            elapsed_time = time.time() - start_time
            
        # Mostrar resultados
        if result["success"]:
            st.success(f"✅ Validación exitosa en {elapsed_time:.2f} segundos")
        else:
            st.error("❌ Se encontraron problemas en la validación")
        
        # Mostrar detalles
        st.subheader("Detalles de la validación")
        
        # Pestañas para diferentes vistas
        tab1, tab2, tab3 = st.tabs(["Resumen", "Log Completo", "Archivo"])
        
        with tab1:
            if result.get("stdout"):
                st.text_area("Salida estándar", result["stdout"], height=200)
            if result.get("stderr"):
                st.text_area("Resultado", result["stderr"], height=200)
        
        with tab2:
            if os.path.exists(result["log_file"]):
                with open(result["log_file"], 'r', encoding='utf-8') as f:
                    log_content = f.read()
                st.download_button("Descargar log completo", log_content, f"validation_{selected_file}.log")
                st.text_area("Log completo", log_content, height=400)
        
        with tab3:
            # Mostrar el contenido del archivo con resaltado de sintaxis
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # Leer solo las primeras 100 líneas
                    lines = []
                    for i, line in enumerate(f):
                        if i >= 100:
                            lines.append("\n...\n(Archivo truncado - mostrando solo las primeras 100 líneas)")
                            break
                        lines.append(line)
                    file_content = "".join(lines)
                    
                # Botón para descarga del archivo completo
                with open(file_path, 'r', encoding='utf-8') as f:
                    complete_content = f.read()
                st.download_button("Descargar archivo completo", complete_content, selected_file)
                
                # Mapear el formato seleccionado a lenguaje para resaltado de sintaxis
                syntax_mapping = {
                    "RDF/XML": "xml",
                    "Turtle": "python",  # Streamlit no tiene soporte específico para Turtle
                    "N-Triples": "text",
                    "TriG": "python",
                    "N-Quads": "text",
                    "JSON-LD": "json"
                }
                
                # Usar el formato seleccionado para determinar el resaltado
                code_language = syntax_mapping.get(syntax, "text")
                st.code(file_content, language=code_language)
            except FileNotFoundError as e:
                st.error(f"Archivo no encontrado: {str(e)}")
            except IOError as e:
                st.error(f"Error de E/S al leer el archivo: {str(e)}")
    
    # Lista de logs anteriores
    st.sidebar.subheader("Logs anteriores")
    log_files = [f for f in os.listdir(LOGS_DIR) if f.startswith("validation_")] if os.path.exists(LOGS_DIR) else []
    log_files.sort(reverse=True)
    
    if log_files:
        selected_log = st.sidebar.selectbox("Seleccionar log", log_files)
        if st.sidebar.button("Ver log seleccionado"):
            log_path = os.path.join(LOGS_DIR, selected_log)
            with open(log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
            st.text_area("Contenido del log", log_content, height=300)
    else:
        st.sidebar.info("No hay logs de validación anteriores")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("Powered by Apache Jena RIOT")
st.sidebar.markdown("[Documentación Apache Jena](https://jena.apache.org/documentation/io/)")