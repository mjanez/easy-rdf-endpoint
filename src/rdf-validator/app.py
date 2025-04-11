import json
import os
import streamlit as st
import pandas as pd
import time
import requests
from datetime import datetime
from urllib.parse import urlparse

# Importar módulos de validación
from app_shacl_results_viewer import display_shacl_results
from riot_validator import validate_riot
from shacl_validator import validate_shacl, get_shacl_results_dataframes
from utils import get_shape_files
from profiles_manager import (
    detect_entity_types,
    get_profile_dropdown_options,
    get_entity_type_dropdown_options,
    parse_profile_selection,
    get_recommendation_message
)
from log import (
    save_validation_log, 
    save_report_content, 
    clear_logs, 
    get_logs,
    format_log_option
)
from config import (
    APP_DIR,
    SHACL_DIR,
    LOGS_DIR,
    TEMP_DIR
)

# Inicializar las claves de estado de sesión que necesitamos
if 'profile_info' not in st.session_state:
    st.session_state.profile_info = None
    
if 'file_path' not in st.session_state:
    st.session_state.file_path = None

if 'file_name' not in st.session_state:
    st.session_state.file_name = None

if 'downloaded_file' not in st.session_state:
    st.session_state.downloaded_file = None

if 'validation_result' not in st.session_state:
    st.session_state.validation_result = None

if 'violations_entity_filter' not in st.session_state:
    st.session_state.violations_entity_filter = []

if 'violations_property_filter' not in st.session_state:
    st.session_state.violations_property_filter = []
    
if 'warnings_entity_filter' not in st.session_state:
    st.session_state.warnings_entity_filter = []

if 'warnings_property_filter' not in st.session_state:
    st.session_state.warnings_property_filter = []

def update_violations_entity_filter():
    st.session_state.violations_entity_filter = st.session_state.get('violations_entity_filter_widget', [])

def update_violations_property_filter():
    st.session_state.violations_property_filter = st.session_state.get('violations_property_filter_widget', [])

def update_warnings_entity_filter():
    st.session_state.warnings_entity_filter = st.session_state.get('warnings_entity_filter_widget', [])

def update_warnings_property_filter():
    st.session_state.warnings_property_filter = st.session_state.get('warnings_property_filter_widget', [])

# Inicialización después de configuración de página
st.set_page_config(
    page_title="RDF/XML Validator",
    page_icon="✅",
    layout="wide"
)

st.title("RDF Validator")
st.write("Valida archivos RDF utilizando [Apache Jena RIOT](https://jena.apache.org/documentation/io/) y [SHACL](https://www.w3.org/TR/shacl/).")


st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 380px !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# Función para listar archivos RDF
def list_rdf_files():
    if not os.path.exists(APP_DIR):
        return []
    return [f for f in os.listdir(APP_DIR) if f.endswith(('.rdf', '.xml', '.ttl', '.n3', '.nt', '.jsonld'))]

# Función para descargar RDF desde URL
def download_rdf_from_url(url):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Extraer el nombre del archivo de la URL o usar un nombre predeterminado
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    if not filename or '.' not in filename:
        # Si no hay nombre de archivo o extensión, usar predeterminado
        filename = f"downloaded_rdf_{timestamp}.ttl"
    
    temp_file_path = os.path.join(TEMP_DIR, filename)
    
    try:
        # Configurar headers para solicitar RDF
        headers = {
            'Accept': 'text/turtle, application/rdf+xml, application/n-triples, application/ld+json'
        }
        
        # Realizar la solicitud HTTP
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Lanzar excepción para códigos de error HTTP
        
        # Guardar el contenido en un archivo temporal
        with open(temp_file_path, 'wb') as f:
            f.write(response.content)
        
        return {
            "success": True,
            "file_path": temp_file_path,
            "content_type": response.headers.get('Content-Type', '')
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Error al descargar el RDF: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error inesperado: {str(e)}"
        }

# UI principal
st.sidebar.header("Opciones de Validación")

# Selector de fuente de datos
data_source = st.sidebar.radio(
        "Fuente de datos RDF",
        options=["Archivo local", "URL externa"],
        horizontal=True
)

# Variable para almacenar la ruta del archivo a validar

if data_source == "Archivo local":
    # Lista de archivos RDF disponibles
    files = list_rdf_files()
    if not files:
        st.warning("No se encontraron archivos RDF en el directorio de datos.")
    else:
        # Actualizar file_name y file_path en session_state
        selected_file = st.sidebar.selectbox("Seleccionar archivo RDF", files)
        if selected_file != st.session_state.file_name:
            st.session_state.file_name = selected_file
            st.session_state.file_path = os.path.join(APP_DIR, selected_file)
            # Limpiar cualquier archivo descargado previo
            st.session_state.downloaded_file = None
else:  # URL externa
    rdf_url = st.sidebar.text_input("URL del RDF", "https://example.org/data.ttl")
    
    if st.sidebar.button("Descargar RDF"):
        with st.spinner('Descargando RDF desde URL...'):
            download_result = download_rdf_from_url(rdf_url)
            
        if download_result["success"]:
            st.sidebar.success("✅ RDF descargado correctamente")
            # Guardar en session_state
            st.session_state.downloaded_file = download_result["file_path"]
            st.session_state.file_path = download_result["file_path"]
            st.session_state.file_name = os.path.basename(download_result["file_path"])
        else:
            st.sidebar.error(f"❌ {download_result['error']}")

# Solo permitir validación si tenemos un archivo (ahora usando session_state)
if st.session_state.file_path:
    # Mostrar el archivo actualmente seleccionado para mayor claridad
    st.sidebar.info(f"📄 Archivo actual: **{os.path.basename(st.session_state.file_path)}**")
    
    # Radio para elegir tipo de validación
    validation_type = st.sidebar.radio(
        "Tipo de validación",
        options=["Sintaxis (RIOT)", "Semántica (SHACL)"],
        horizontal=True,
        help="Sintaxis: Valida la estructura RDF con Apache Jena RIOT. Semántica: Valida el contenido según reglas SHACL."
    )

    # Siempre usar None para logs_dir
    logs_dir_to_use = None
    
    if validation_type == "Sintaxis (RIOT)":
        # Opciones de validación RIOT
        base_uri = st.sidebar.text_input("Base URI", value="http://datos.gob.es/catalogo")
        syntax_options = ["RDF/XML", "Turtle", "N-Triples", "TriG", "N-Quads", "JSON-LD"]
        syntax = st.sidebar.selectbox("Formato de sintaxis", syntax_options)
        
        # Botón para ejecutar validación
        if st.sidebar.button("Validar RDF"):
            with st.spinner('Validando sintaxis RDF...'):
                start_time = time.time()
                # Usar la configuración de logs y st.session_state.file_path
                result = validate_riot(st.session_state.file_path, base_uri, syntax, logs_dir=logs_dir_to_use)
                elapsed_time = time.time() - start_time

                if "log_content" in result:
                    # Crear metadatos para el log
                    metadata = {
                        "Archivo": os.path.basename(st.session_state.file_path),
                        "Sintaxis": syntax,
                        "Base URI": base_uri,
                        "Resultado": "Exitoso" if result["success"] else "Fallido",
                        "Tiempo": f"{elapsed_time:.2f} segundos"
                    }
                    
                    # Guardar en la sesión del navegador
                    save_validation_log(
                        validation_type="RIOT",
                        file_name=st.session_state.file_path,
                        log_content=result["log_content"], 
                        metadata=metadata,
                        logs_dir=logs_dir_to_use  # Esto ya lo tenías configurado
                    )
                
            # Mostrar resultados
            if result["success"]:
                st.success(f"✅ Validación sintáctica exitosa en {elapsed_time:.2f} segundos")
            else:
                st.error("❌ Se encontraron problemas en la validación sintáctica")
            
            # Mostrar detalles
            st.subheader("Detalles de la validación sintáctica")
            
            # Pestañas para diferentes vistas
            tab1, tab2, tab3 = st.tabs(["Resumen", "Log Completo", "Archivo"])
            
            with tab1:
                if result.get("stdout"):
                    st.text_area("Salida estándar", result["stdout"], height=200)
                if result.get("stderr"):
                    st.text_area("Resultado", result["stderr"], height=200)
            
            with tab2:
                # Si hay archivo de log y existe, leerlo
                if "log_file" in result and result["log_file"] and os.path.exists(result["log_file"]):
                    with open(result["log_file"], 'r', encoding='utf-8') as f:
                        log_content = f.read()
                    st.text_area("Informe Turtle (TTL)", log_content, height=400)
                # Si no hay archivo pero hay contenido de log
                elif "log_content" in result and result["log_content"]:
                    st.text_area("Informe Turtle (TTL)", result["log_content"], height=400)
                else:
                    st.warning("No se encontró un log detallado de la validación")
            
            with tab3:
                # Mostrar el contenido del archivo con resaltado de sintaxis
                try:
                    with open(st.session_state.file_path, 'r', encoding='utf-8') as f:
                        # Leer solo las primeras 50 líneas
                        lines = []
                        lines.append("[Archivo truncado - mostrando solo las primeras 50 líneas]\n\n")
                        for i, line in enumerate(f):
                            if i >= 50:
                                lines.append("\n...\n")
                                break
                            lines.append(line)
                        file_content = "".join(lines)
                        
                    # Botón para descarga del archivo completo
                    with open(st.session_state.file_path, 'r', encoding='utf-8') as f:
                        complete_content = f.read()
                    st.download_button("Descargar archivo completo", complete_content, st.session_state.file_name)
                    
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
    
    # En la sección de validación SHACL - ACTUALIZADA para usar la nueva configuración
    else:  # Validación SHACL
        # Detectar tipos de entidad en el archivo RDF
        with st.spinner('Analizando RDF para detectar tipos de entidad...'):
            detected_entities = detect_entity_types(st.session_state.file_path)
        
        # Filtrar solo tipos que existen en el archivo
        available_entity_types = [t for t, uris in detected_entities.items() if uris]
        
        # En app.py - Mostrar resumen de entidades detectadas sin usar la columna "Destacado"
        # Mostrar resumen de entidades detectadas en una sola tabla
        if any(len(uris) > 0 for uris in detected_entities.values()):
            # Crear un diccionario para la tabla, ahora sin la columna "Destacado"
            entity_table_data = {
                "Tipo de Entidad": [],
                "Cantidad": []
            }
            
            # Llenar con datos de todas las entidades detectadas
            for entity_type, uris in detected_entities.items():
                if len(uris) > 0:  # Solo mostrar entidades que existen en el documento
                    entity_table_data["Tipo de Entidad"].append(entity_type)
                    entity_table_data["Cantidad"].append(len(uris))

            df_entities = pd.DataFrame(entity_table_data)
       
            # Crear y mostrar la tabla con estilos
            st.sidebar.subheader("Entidades detectadas:")            
            st.sidebar.dataframe(
                df_entities,
                hide_index=True,
                use_container_width=True
            )
        else:
            st.sidebar.warning("No se detectaron entidades DCAT en el archivo")
        
        # Obtener opciones de perfiles organizados jerárquicamente
        profile_options = get_profile_dropdown_options()
        
        # Lista desplegable para seleccionar perfil
        st.sidebar.subheader("Selección de perfil")
        
        # Selector de perfil principal
        profile_group = st.sidebar.selectbox(
            "Perfil DCAT",
            options=list(profile_options.keys()),
            help="Selecciona el perfil y versión a utilizar"
        )
        
        # Selector de caso de validación dentro del perfil seleccionado
        case_options = profile_options.get(profile_group, [])
        default_index = next((i for i, option in enumerate(case_options) if option.get("recommended")), 0)
        
        selected_profile_case = st.sidebar.selectbox(
            "Caso de validación",
            options=[option["value"] for option in case_options],
            format_func=lambda x: next((option["label"] for option in case_options if option["value"] == x), x),
            index=default_index,
            help="Selecciona el caso de validación específico"
        )
        
        # Parsear la selección de perfil
        profile, version, case = parse_profile_selection(selected_profile_case)
        
        # Mostrar descripción del caso seleccionado
        if profile and version and case:
            recommendation = get_recommendation_message(profile, version, case)
            st.sidebar.info(recommendation)

        # Selector de tipo de entidad si es necesario (para DCAT-AP-ES)
        selected_entity_type = None
        if profile in ["DCAT-AP-ES", "NTI-RISP"] and available_entity_types:
            entity_options = get_entity_type_dropdown_options(profile, version, case)
            
            # Filtrar solo los tipos de entidad que están en el archivo RDF
            # Añadir siempre "Todas" como opción disponible
            available_options = [
                option for option in entity_options 
                if option["value"] == "Todas" or option["value"] in available_entity_types
            ]
            
            if available_options:
                # Encontrar el índice de "Todas" para usarlo como valor predeterminado
                default_index = next(
                    (i for i, option in enumerate(available_options) if option["value"] == "Todas"), 
                    0
                )
                
                selected_entity_type = st.sidebar.selectbox(
                    "Tipo de entidad a validar",
                    options=[option["value"] for option in available_options],
                    format_func=lambda x: next((option["label"] for option in available_options if option["value"] == x), x),
                    index=default_index,
                    help="Selecciona el tipo de entidad que deseas validar específicamente o 'Todas' para validar todo el documento"
                )
        
        # Botón para ejecutar validación SHACL
        if st.sidebar.button("Validar con SHACL"):
            with st.spinner('Preparando validación SHACL...'):
                # Código de validación existente...
                shape_files = get_shape_files(profile, version, case, selected_entity_type)
                
                if not shape_files:
                    st.error("❌ No se encontraron archivos SHACL para el perfil seleccionado")
                else:
                    # Guardar información del perfil en session_state
                    profile_info = f"{profile} {version}"
                    if case:
                        profile_info += f" - {case}"
                    if selected_entity_type:
                        profile_info += f" - {selected_entity_type}"
                        
                    st.session_state.profile_info = profile_info
                        
                    # Ejecutar validación
                    start_time = time.time()
                    result = validate_shacl(st.session_state.file_path, shape_files, logs_dir=logs_dir_to_use, temp_dir=TEMP_DIR)
                    st.session_state.validation_result = result
                    elapsed_time = time.time() - start_time

                    # Guardar el log y el informe en la sesión del navegador
                    if "log_content" in result:
                        # Crear metadatos para el log
                        metadata = {
                            "Archivo": os.path.basename(st.session_state.file_path),
                            "Perfil": f"{profile} {version}",
                            "Caso": case,
                            "Entidad": selected_entity_type if selected_entity_type else "Todas",
                            "Resultado": "Conforme" if result.get("success", False) else "No conforme",
                            "Nivel": result.get("conformance_level", "violations"),
                            "Tiempo": f"{elapsed_time:.2f} segundos"
                        }
                        
                        # Añadir estadísticas si están disponibles
                        if "validation_details" in result:
                            metadata["Violaciones"] = result["validation_details"]["violations_count"]
                            metadata["Advertencias"] = result["validation_details"]["warnings_count"]
                        
                        # Para la validación SHACL y su informe (usar la función de log.py que ya gestiona st.session_state)
                        save_validation_log(
                            validation_type="SHACL-LOG",
                            file_name=st.session_state.file_path,
                            log_content=result["log_content"],
                            metadata=metadata,
                            logs_dir=logs_dir_to_use
                        )
                    
                        # Guardar también el informe si está disponible
                        if "report_content" in result and result["report_content"]:
                            save_report_content(
                                validation_type="SHACL-REPORT",
                                file_name=st.session_state.file_path,
                                report_content=result["report_content"],
                                metadata=metadata,
                                logs_dir=logs_dir_to_use
                            )
                        
        # Llamar a la función para mostrar resultados si existen
        display_shacl_results(profile, version, case, selected_entity_type)

# Historial de validaciones
st.sidebar.subheader("Historial de validaciones")

# En lugar de tener pestañas, mostrar directamente los logs de la sesión
logs = get_logs()
if not logs:
    st.sidebar.info("**No hay validaciones en la sesión actual**\n\nLos logs se guardan en la sesión del navegador y se perderán al cerrar o recargar la página.")
else:
    log_options = [format_log_option(log) for log in logs]
    
    selected_log_index = st.sidebar.selectbox(
        "Validaciones recientes",
        range(len(log_options)),
        format_func=lambda i: log_options[i]
    )

    # Obtener el log seleccionado directamente (sin necesidad de botón adicional)
    log_data = logs[selected_log_index]
    
    # Mostrar metadatos si existen
    if "metadata" in log_data:
        meta = log_data["metadata"]
        meta_text = "\n".join([f"**{k}:** {v}" for k, v in meta.items()])
        st.sidebar.info(meta_text)
    
    st.sidebar.text_area(
        f"Log de validación ({log_data['timestamp']})",
        log_data['content'],
        height=250
    )
    
    # Ofrecer descarga del log
    st.sidebar.download_button(
        "Descargar log",
        log_data['content'],
        f"{log_data['name']}.txt",
        help="Descargar el contenido del log seleccionado"
    )

# Botón para limpiar todos los logs de la sesión
if st.sidebar.button("Limpiar historial de sesión"):
    clear_logs()
    st.rerun()

# Limpieza de archivos temporales (mantener los últimos 10)
def cleanup_files():
    """Limpia archivos temporales y mantiene el sistema ordenado"""
    # Siempre limpiar archivos temporales
    if os.path.exists(TEMP_DIR):
        all_temp_files = sorted(
            [os.path.join(TEMP_DIR, f) for f in os.listdir(TEMP_DIR)], 
            key=os.path.getctime
        )
        
        # Mantener solo los 10 archivos más recientes
        if len(all_temp_files) > 10:
            for old_file in all_temp_files[:-10]:
                try:
                    os.remove(old_file)
                except OSError:
                    pass

# Footer
st.sidebar.markdown("---")
st.sidebar.info("Powered by [Apache Jena RIOT](https://jena.apache.org/documentation/io/) & [SHACL](https://www.w3.org/TR/shacl/)")