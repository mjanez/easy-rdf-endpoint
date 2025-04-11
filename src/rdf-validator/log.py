"""
Gestión simplificada de logs para el validador RDF.
Los logs se mantienen solo en la sesión de Streamlit y se perderán al cerrar o recargar la página.
"""
from datetime import datetime
import streamlit as st
import os

# Máximo número de logs a mantener en la sesión
MAX_LOGS = 10
# Máxima longitud para truncar contenido largo
MAX_CONTENT_LENGTH = 10000

def save_validation_log(validation_type, file_name, log_content, metadata=None, logs_dir=None):
    """
    Guarda un log de validación en el estado de sesión de Streamlit.
    
    Args:
        validation_type: Tipo de validación ('RIOT' o 'SHACL')
        file_name: Nombre del archivo validado
        log_content: Contenido del log
        metadata: Diccionario con metadatos adicionales (opcional)
        logs_dir: Parámetro ignorado (mantenido para compatibilidad)
        
    Returns:
        str: ID del log creado
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_id = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Truncar contenido si es muy largo
    if len(log_content) > MAX_CONTENT_LENGTH:
        truncated_content = log_content[:MAX_CONTENT_LENGTH] + "\n...[Contenido truncado]..."
    else:
        truncated_content = log_content
    
    # Crear un ID único basado en timestamp y tipo
    log_id = f"{validation_type}_{timestamp_id}"
    
    # Crear entrada de log
    log_entry = {
        "id": log_id,
        "name": f"validation_{os.path.basename(file_name)}",
        "content": truncated_content,
        "type": validation_type,
        "timestamp": timestamp
    }
    
    # Añadir metadatos si existen
    if metadata:
        log_entry["metadata"] = metadata
    
    # Inicializar el array de logs si no existe
    if 'validation_logs' not in st.session_state:
        st.session_state.validation_logs = []
    
    # Añadir el nuevo log al inicio de la lista
    st.session_state.validation_logs.insert(0, log_entry)
    
    # Mantener solo los N logs más recientes
    if len(st.session_state.validation_logs) > MAX_LOGS:
        st.session_state.validation_logs = st.session_state.validation_logs[:MAX_LOGS]
    
    return log_id

def save_report_content(validation_type, file_name, report_content, metadata=None, logs_dir=None):
    """
    Guarda el contenido de un informe (por ejemplo, informe SHACL en TTL).
    
    Args:
        validation_type: Tipo de validación ('SHACL-REPORT')
        file_name: Nombre del archivo validado
        report_content: Contenido del informe
        metadata: Diccionario con metadatos adicionales (opcional)
        logs_dir: Parámetro ignorado (mantenido para compatibilidad)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_id = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Truncar contenido si es muy largo
    if len(report_content) > MAX_CONTENT_LENGTH:
        truncated_content = report_content[:MAX_CONTENT_LENGTH] + "\n...[Contenido truncado]..."
    else:
        truncated_content = report_content
    
    # Crear entrada de log
    report_id = f"{validation_type}_{timestamp_id}"
    report_entry = {
        "id": report_id,
        "name": f"report_{os.path.basename(file_name)}",
        "content": truncated_content,
        "type": validation_type,
        "timestamp": timestamp
    }
    
    # Añadir metadatos si existen
    if metadata:
        report_entry["metadata"] = metadata
    
    # Inicializar el array de logs si no existe
    if 'validation_logs' not in st.session_state:
        st.session_state.validation_logs = []
    
    # Añadir el nuevo log al inicio de la lista
    st.session_state.validation_logs.insert(0, report_entry)
    
    # Mantener solo los N logs más recientes
    if len(st.session_state.validation_logs) > MAX_LOGS:
        st.session_state.validation_logs = st.session_state.validation_logs[:MAX_LOGS]

def clear_logs():
    """
    Limpia todos los logs de la sesión.
    """
    st.session_state.validation_logs = []

def get_logs():
    """
    Obtiene los logs almacenados en la sesión.
    
    Returns:
        list: Lista de logs
    """
    if 'validation_logs' not in st.session_state:
        st.session_state.validation_logs = []
    
    return st.session_state.validation_logs

def format_log_option(log):
    """
    Formatea un log para mostrarlo en un selector.
    
    Args:
        log: Entrada de log
        
    Returns:
        str: Texto formateado para mostrar
    """
    # Determinar icono según tipo
    icon = "📝"  # Default
    if log['type'].startswith('RIOT'):
        icon = "📝"
    elif log['type'].startswith('SHACL'):
        icon = "📊"
    
    # Extraer nombre de archivo
    file_name = os.path.basename(log['name'])
    
    # Formatear resultado si está en metadatos
    result = ""
    if "metadata" in log and "Resultado" in log["metadata"]:
        result_text = log["metadata"]["Resultado"]
        if "Conforme" in result_text or "Exitoso" in result_text:
            result = " ✓"
        else:
            result = " ✗"
    
    return f"{icon} {log['timestamp']} - {file_name}{result}"