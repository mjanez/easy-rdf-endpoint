import os
import subprocess
import tempfile
from datetime import datetime

def validate_riot(file_path, base_uri="", syntax="RDF/XML", logs_dir=None):
    """
    Valida un archivo RDF usando Apache Jena RIOT.
    
    Args:
        file_path: Ruta al archivo RDF a validar
        base_uri: URI base para la validación
        syntax: Formato de sintaxis (RDF/XML, Turtle, etc.)
        logs_dir: Parámetro ignorado, mantenido por compatibilidad
        
    Returns:
        dict: Resultado de la validación con stdout, stderr y contenido del log
    """
    # Usar siempre archivo temporal
    temp_log = tempfile.NamedTemporaryFile(delete=False, suffix='.log')
    log_file = temp_log.name
    temp_log.close()
    
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
        
        # Guardar log en el archivo temporal
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"COMMAND: {' '.join(cmd)}\n")
            f.write(f"STDOUT:\n{validation_result.stdout}\n")
            f.write(f"STDERR:\n{validation_result.stderr}\n")
            f.write(f"EXIT CODE: {validation_result.returncode}\n")
        
        # Leer el contenido del log para devolverlo
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Limpiar el archivo temporal
        try:
            os.unlink(log_file)
        except:
            pass  # Ignorar errores al eliminar
        
        return {
            "success": validation_result.returncode == 0,
            "stdout": validation_result.stdout,
            "stderr": validation_result.stderr,
            "log_file": None,  # Ya no devolvemos ruta a archivo de logs
            "log_content": log_content  # Contenido del log para mostrarlo
        }
    except subprocess.CalledProcessError as e:
        error_msg = f"Error executing command: {str(e)}"
        # Guardar log de error en archivo temporal
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"COMMAND: {' '.join(cmd)}\n")
            f.write(f"ERROR: {error_msg}\n")
            f.write(f"STDOUT:\n{e.stdout}\n")
            f.write(f"STDERR:\n{e.stderr}\n")
        
        # Leer el contenido del log para devolverlo
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Limpiar el archivo temporal
        try:
            os.unlink(log_file)
        except:
            pass  # Ignorar errores al eliminar
        
        return {
            "success": False,
            "stderr": error_msg,
            "log_file": None,
            "log_content": log_content
        }
    except FileNotFoundError as e:
        error_msg = f"Command not found: {str(e)}"
        # Guardar log de error en archivo temporal
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"COMMAND: {' '.join(cmd)}\n")
            f.write(f"ERROR: {error_msg}\n")
        
        # Leer el contenido del log para devolverlo
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Limpiar el archivo temporal
        try:
            os.unlink(log_file)
        except:
            pass  # Ignorar errores al eliminar
        
        return {
            "success": False,
            "stderr": error_msg,
            "log_file": None,
            "log_content": log_content
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        # Guardar log de error en archivo temporal
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"COMMAND: {' '.join(cmd)}\n")
            f.write(f"ERROR: {error_msg}\n")
        
        # Leer el contenido del log para devolverlo
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Limpiar el archivo temporal
        try:
            os.unlink(log_file)
        except:
            pass  # Ignorar errores al eliminar
        
        return {
            "success": False,
            "stderr": error_msg,
            "log_file": None,
            "log_content": log_content
        }