import os
import subprocess
from datetime import datetime
import re
import hashlib
import tempfile

import pandas as pd
import rdflib
from rdflib import Graph, Namespace
from rdflib.namespace import RDF

from config import (
    SHAPES_CACHE,
    SHACL_DIR,
    PREFIXES,
    ONTOLOGIES_DIR,
    PROFILES,
    # Namespaces
    DCAT,
    DCT,
    FOAF,
    LOCN,
    RDF,
    SPDX,
    TIME,
    VCARD
)

# Namespaces utilizados en informes SHACL
SH = Namespace("http://www.w3.org/ns/shacl#")

def get_combined_shapes(shape_files, temp_dir):
    """
    Combina múltiples archivos SHACL en un solo grafo.
    Utiliza caché para mejorar rendimiento.
    
    Args:
        shape_files: Lista de rutas a archivos de shapes SHACL
        temp_dir: Directorio para archivos temporales
        
    Returns:
        str: Ruta al archivo combinado
    """
    if not shape_files:
        return None
    
    # Generar una clave de caché basada en los archivos y sus fechas de modificación
    cache_key = hashlib.md5(
        "_".join([f"{f}_{os.path.getmtime(f)}" for f in shape_files if os.path.exists(f)])
        .encode()
    ).hexdigest()
    
    # Comprobar si ya existe en caché
    if cache_key in SHAPES_CACHE:
        if os.path.exists(SHAPES_CACHE[cache_key]):
            return SHAPES_CACHE[cache_key]
    
    # Si no está en caché, combinar los archivos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    combined_file = f"{temp_dir}/combined_shapes_{timestamp}.ttl"
    
    try:
        # Crear un grafo RDF y cargar todos los archivos
        g = Graph()
        
        for shape_file in shape_files:
            if os.path.exists(shape_file):
                g.parse(shape_file, format="turtle")
        
        # Serializar el grafo combinado
        g.serialize(destination=combined_file, format="turtle")
        
        # Guardar en caché
        SHAPES_CACHE[cache_key] = combined_file
        
        return combined_file
    except Exception as e:
        print(f"Error al combinar shapes: {str(e)}")
        
        # Si falla, usar el primer archivo
        for shape_file in shape_files:
            if os.path.exists(shape_file):
                return shape_file
        
        return None

def filter_known_warnings(stderr_content):
    """
    Filtra advertencias conocidas de descarga de ontologías que no afectan el resultado.
    
    Args:
        stderr_content: Contenido de error estándar del comando SHACL
        
    Returns:
        str: Contenido filtrado
    """
    if not stderr_content:
        return ""
        
    lines = stderr_content.split('\n')
    filtered_lines = []
    
    skip_next_lines = 0
    known_errors = [
        "An error occurred while attempting to read from https://schema.org/version/latest/schema.ttl",
        "An error occurred while attempting to read from http://purl.org/dc/terms/",
        "HTTP Exception: 404 - Not Found",
        "HTTP Exception: 303 - See Other",
        "WARN  OntDocumentManager",  # Capturar advertencias generales del OntDocumentManager
        "org.apache.jena.atlas.web.HttpException"  # Capturar excepciones HTTP de Jena
    ]
    
    stacktrace_indicators = [
        "\tat ",  # Patrón Java para líneas de stack trace
        "~[",     # Indicador de biblioteca JAR en stack trace
        "org.apache.jena"  # Paquetes de Jena en stack trace
    ]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Si estamos saltando líneas debido a un error conocido
        if skip_next_lines > 0:
            skip_next_lines -= 1
            i += 1
            continue
            
        # Verificar si es una línea de error conocido
        is_known_error = any(error in line for error in known_errors)
        
        if is_known_error:
            # Buscar cuántas líneas ocupa el stacktrace
            j = i + 1
            stacktrace_lines = 0
            while j < len(lines) and any(indicator in lines[j] for indicator in stacktrace_indicators):
                stacktrace_lines += 1
                j += 1
                
            # Saltar esta línea y el stacktrace
            skip_next_lines = stacktrace_lines
            i += 1
            continue
            
        filtered_lines.append(line)
        i += 1
    
    return '\n'.join(filtered_lines)

def validate_shacl(data_file, shape_files, logs_dir=None, temp_dir=None):
    """
    Valida un archivo RDF contra un conjunto de shapes SHACL.
    
    Args:
        data_file: Ruta al archivo de datos RDF
        shape_files: Lista de rutas a archivos de shapes SHACL
        logs_dir: Parámetro ignorado, mantenido por compatibilidad
        temp_dir: Directorio para archivos temporales
        
    Returns:
        dict: Resultado de la validación con información detallada
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Usar siempre archivos temporales que serán eliminados después
    temp_log = tempfile.NamedTemporaryFile(delete=False, suffix='.log')
    log_file = temp_log.name
    temp_log.close()
    
    temp_ttl = tempfile.NamedTemporaryFile(delete=False, suffix='.ttl')
    result_ttl_file = temp_ttl.name
    temp_ttl.close()
    
    # Detectar la extensión del archivo y convertirlo a TTL si es necesario
    file_ext = os.path.splitext(data_file)[1].lower()
    
    use_temp_file = file_ext != '.ttl'
    temp_ttl_file = None
    
    try:
        # Si no es TTL, convertir a TTL primero
        if use_temp_file:
            temp_ttl_file = f"{temp_dir}/temp_{timestamp}.ttl"
            
            # Usar riot para convertir a Turtle
            with open(temp_ttl_file, 'w') as out_file:
                convert_process = subprocess.run(
                    ["riot", "--output=TTL", data_file],
                    stdout=out_file,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            if convert_process.returncode != 0:
                # Preparar mensaje de error
                error_msg = f"Error al convertir archivo a formato Turtle: {convert_process.stderr}"
                
                # Guardar log de error
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(f"ERROR: {error_msg}\n")
                
                # Leer contenido del log para devolverlo
                log_content = ""
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        log_content = f.read()
                except:
                    pass
                    
                # Limpiar archivos temporales si no estamos guardando en servidor
                try:
                    os.unlink(log_file)
                    os.unlink(result_ttl_file)
                except:
                    pass
                
                return {
                    "success": False,
                    "stderr": error_msg,
                    "log_file": None,
                    "log_content": log_content
                }
            
            # Usar el archivo temporal para la validación
            input_file = temp_ttl_file
        else:
            input_file = data_file
        
        # Cargar el archivo RDF original para recuperar información de tipos
        original_graph = Graph()
        try:
            original_graph.parse(input_file, format="turtle")
        except Exception as e:
            print(f"Error al cargar archivo RDF original para detectar tipos: {e}")
            original_graph = None
            
        # Combinar los archivos SHACL si es necesario
        if len(shape_files) > 1:
            shapes_file = get_combined_shapes(shape_files, temp_dir)
        else:
            shapes_file = shape_files[0] if shape_files else None
            
        if not shapes_file:
            # Preparar mensaje de error
            error_msg = "No se encontraron archivos SHACL válidos"
            
            # Guardar log de error
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"ERROR: {error_msg}\n")
                
            # Leer contenido del log para devolverlo
            log_content = ""
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
            except:
                pass
                
            # Limpiar archivos temporales si no estamos guardando en servidor
            try:
                os.unlink(log_file)
                os.unlink(result_ttl_file)
            except:
                pass
                    
            return {
                "success": False,
                "stderr": error_msg,
                "log_file": None,
                "log_content": log_content
            }
        
        # Construir comando shaclvalidate correcto
        cmd = [
            "shaclvalidate.sh", 
            "-datafile", input_file,
            "-shapesfile", shapes_file
        ]

        # Antes de ejecutar el comando, configurar variables de entorno
        env = os.environ.copy()
        
        # Configurar Jena para usar la caché local de ontologías
        # y la política de carga personalizada
        env["JENA_ONTOLOGY_PATH"] = ONTOLOGIES_DIR
        env["JVM_ARGS"] = f"-Djena.ontology.OntModelSpec.ont-policy=file://{ONTOLOGIES_DIR}/ont-policy.ttl"
        env["JENA_IGNORE_IMPORTS"] = "false"  # Ahora podemos habilitar importaciones
        
        # Y actualizar el comando para usar este entorno
        validation_result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,  # Explícitamente no lanzar excepción si falla
            env=env  # Usar el entorno modificado
        )
        
        # Guardar el informe en un archivo TTL
        with open(result_ttl_file, 'w', encoding='utf-8') as f:
            f.write(validation_result.stdout)
        
        # Filtrar advertencias conocidas que no afectan el resultado
        filtered_stderr = filter_known_warnings(validation_result.stderr)
        
        # Analizar el informe para extraer violaciones y advertencias
        validation_details = parse_shacl_report(validation_result.stdout, original_graph)
        
        # Interpretamos los resultados siguiendo la especificación SHACL
        # 1. conforms: false indica incumplimiento pero puede ser solo warnings
        # 2. violations: errores graves que hacen que el documento no sea válido
        # 3. warnings: recomendaciones que no invalidan el documento
        conforms = validation_details["conforms"]
        has_violations = validation_details["violations_count"] > 0
        has_warnings = validation_details["warnings_count"] > 0
        
        # Determinar nivel de conformidad:
        # - Totalmente conforme: conforms=true, sin violaciones ni warnings
        # - Conforme con advertencias: sin violaciones pero con warnings
        # - No conforme: con violaciones (independiente de warnings)
        if conforms and not has_violations and not has_warnings:
            conformance_level = "full"  # Totalmente conforme
            success = True
        elif not has_violations and has_warnings:
            conformance_level = "warnings"  # Conforme con advertencias
            success = True  # Es válido aunque tenga warnings
        else:
            conformance_level = "violations"  # No conforme
            success = False
        
        # Guardar log
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"COMMAND: {' '.join(cmd)}\n")
            if use_temp_file:
                f.write(f"ORIGINAL FILE: {data_file} (convertido a Turtle)\n")
            f.write(f"SHAPES FILES: {', '.join(shape_files)}\n")
            f.write(f"COMBINED SHAPES: {shapes_file}\n")
            f.write(f"STDOUT:\n{validation_result.stdout}\n")
            f.write(f"STDERR:\n{validation_result.stderr}\n")
            f.write(f"EXIT CODE: {validation_result.returncode}\n")
            f.write(f"VALIDATION RESULT: {'Conforme' if success else 'No conforme'}\n")
            f.write(f"CONFORMANCE LEVEL: {conformance_level}\n")
            f.write(f"REPORT FILE: {result_ttl_file}\n")
            f.write(f"VIOLATIONS: {validation_details['violations_count']}\n")
            f.write(f"WARNINGS: {validation_details['warnings_count']}\n")
        
        # Leer el contenido del log y el informe para devolverlos
        log_content = ""
        report_content = ""
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
                
            with open(result_ttl_file, 'r', encoding='utf-8') as f:
                report_content = f.read()
        except Exception as e:
            print(f"Error al leer archivos de log/informe: {e}")
        
        # Limpiar los archivos temporales si no estamos guardando en servidor
        if not logs_dir:
            for temp_file in [log_file, result_ttl_file]:
                try:
                    os.unlink(temp_file)
                except:
                    pass
        
        return {
            "success": success,
            "stdout": validation_result.stdout,
            "stderr": filtered_stderr,
            "log_file": None,
            "report_file": None,
            "log_content": log_content,
            "report_content": report_content,
            "validation_details": validation_details,
            "shapes_files": shape_files,
            "combined_shapes": shapes_file,
            "conformance_level": conformance_level
        }
    except subprocess.CalledProcessError as e:
        error_msg = f"Error executing SHACL command: {str(e)}"
        # Guardar log de error
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"COMMAND: {' '.join(cmd)}\n")
            f.write(f"SHAPES FILES: {', '.join(shape_files)}\n")
            f.write(f"ERROR: {error_msg}\n")
            f.write(f"STDOUT:\n{e.stdout if hasattr(e, 'stdout') else ''}\n")
            f.write(f"STDERR:\n{e.stderr if hasattr(e, 'stderr') else ''}\n")
        
        # Leer el contenido del log para devolverlo
        log_content = ""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
        except:
            pass
            
        # Limpiar los archivos temporales si no estamos guardando en servidor
        try:
            os.unlink(log_file)
            os.unlink(result_ttl_file)
        except:
            pass
        
        return {
            "success": False,
            "stderr": error_msg,
            "log_file": None,
            "log_content": log_content
        }
    except FileNotFoundError as e:
        error_msg = f"SHACL command not found: {str(e)}"
        # Guardar log de error
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"COMMAND: {' '.join(cmd)}\n")
            f.write(f"SHAPES FILES: {', '.join(shape_files)}\n")
            f.write(f"ERROR: {error_msg}\n")
        
        # Leer el contenido del log para devolverlo
        log_content = ""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
        except:
            pass
            
        # Limpiar los archivos temporales si no estamos guardando en servidor
        try:
            os.unlink(log_file)
            os.unlink(result_ttl_file)
        except:
            pass
        
        return {
            "success": False,
            "stderr": error_msg,
            "log_file": None,
            "log_content": log_content
        }
    except Exception as e:
        error_msg = f"Unexpected SHACL error: {str(e)}"
        # Guardar log de error
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"SHAPES FILES: {', '.join(shape_files)}\n")
            f.write(f"ERROR: {error_msg}\n")
        
        # Leer el contenido del log para devolverlo
        log_content = ""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
        except:
            pass
            
        # Limpiar los archivos temporales si no estamos guardando en servidor
        try:
            os.unlink(log_file)
            os.unlink(result_ttl_file)
        except:
            pass
        
        return {
            "success": False,
            "stderr": error_msg,
            "log_file": None,
            "log_content": log_content
        }
    finally:
        # Eliminar archivo temporal de conversión si existe
        if temp_ttl_file and os.path.exists(temp_ttl_file):
            try:
                os.remove(temp_ttl_file)
            except:
                pass  # Ignorar errores al eliminar archivo temporal

def parse_shacl_report(report_content, original_graph=None):
    """
    Analiza el informe SHACL en formato Turtle para extraer violaciones y advertencias.
    
    Args:
        report_content: Contenido del informe SHACL en formato Turtle
        original_graph: Grafo RDF original para extraer información de tipos
        
    Returns:
        dict: Detalles de violaciones y advertencias
    """
    # Intentar analizar con rdflib si está disponible
    try:
        return parse_with_rdflib(report_content, original_graph)
    except Exception as e:
        print(f"Error parsing with rdflib: {str(e)}")
        # Fallback a regex si rdflib falla
        return parse_with_regex(report_content)


def parse_with_rdflib(report_content, original_graph=None):
    """
    Utiliza rdflib para analizar el informe SHACL.
    
    Args:
        report_content: Contenido del informe SHACL
        original_graph: Grafo RDF original para consultar tipos
    """
    g = Graph()
    g.parse(data=report_content, format="turtle")
    
    # Buscar el nodo de ValidationReport
    report_node = None
    for s in g.subjects(RDF.type, SH.ValidationReport):
        report_node = s
        break
    
    if not report_node:
        return {
            "conforms": True,
            "violations": [],
            "warnings": [],
            "violations_count": 0,
            "warnings_count": 0
        }
    
    # Verificar si conforms es True
    conforms = False
    for _, _, o in g.triples((report_node, SH.conforms, None)):
        conforms = (str(o).lower() == "true")
    
    # Añadir los namespaces que necesitamos para detectar tipos
    DCAT = Namespace("http://www.w3.org/ns/dcat#")
    FOAF = Namespace("http://xmlns.com/foaf/0.1/")
    DCT = Namespace("http://purl.org/dc/terms/")
    RDF_TYPE = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#").type
    
    # Procesar todos los resultados
    violations = []
    warnings = []
    
    for result in g.objects(report_node, SH.result):
        # Obtener información del resultado
        message = None
        focus_node = None
        result_path = None
        severity = "Violation"  # Por defecto es violación
        value = None  # Campo para sh:value
        
        for _, p, o in g.triples((result, None, None)):
            if p == SH.resultMessage:
                message = str(o)
            elif p == SH.focusNode:
                focus_node = str(o)
            elif p == SH.resultPath:
                # Preservar el valor completo del path como está en el RDF
                result_path = str(o)
                # Si es una URI compleja, intentar extraer más información
                if isinstance(o, rdflib.URIRef):
                    # Intentar buscar propiedades anidadas del path que lleven al valor
                    for _, p2, path_value in g.triples((o, None, None)):
                        if isinstance(path_value, rdflib.URIRef):
                            # Intenta capturar el prefijo:nombre si está disponible
                            path_parts = str(path_value).split('/')
                            if '#' in path_parts[-1]:
                                result_path = path_parts[-1].split('#')[-1]
                            else:
                                result_path = path_parts[-1]
                            # Buscar namespace si está disponible
                            for prefix, namespace in g.namespaces():
                                if str(path_value).startswith(str(namespace)):
                                    local_part = str(path_value)[len(str(namespace)):]
                                    result_path = f"{prefix}:{local_part}"
                                    break
                            break
            elif p == SH.resultSeverity:
                severity = str(o).split("#")[-1]
            elif p == SH.value:  # Extraer el valor que causa la violación
                value = str(o)
        
        # Detectar tipo de entidad del nodo usando el grafo original si está disponible
        entity_type = "Desconocido"
        if focus_node and focus_node != "Desconocido" and original_graph:
            # Intentar convertir focus_node a URIRef para consultas en el grafo
            try:
                focus_uri = rdflib.URIRef(focus_node)
                
                # Buscar todos los tipos RDF para este nodo en el grafo original
                found_type = False
                for _, _, type_uri in original_graph.triples((focus_uri, RDF_TYPE, None)):
                    # Identificar el tipo de entidad basado en las clases DCAT y DCT
                    if type_uri == DCAT.Dataset:
                        entity_type = "Dataset"
                        found_type = True
                        break
                    elif type_uri == DCAT.Catalog:
                        entity_type = "Catalog"
                        found_type = True
                        break
                    elif type_uri == DCAT.Distribution:
                        entity_type = "Distribution"
                        found_type = True
                        break
                    elif type_uri == DCAT.DataService:
                        entity_type = "DataService"
                        found_type = True
                        break
                    elif type_uri == DCAT.CatalogRecord:
                        entity_type = "CatalogRecord"
                        found_type = True
                        break
                    elif type_uri == DCT.PeriodOfTime:
                        entity_type = "PeriodOfTime"
                        found_type = True
                        break
                
                # Si no encontramos un tipo directo, buscar tipos a través de relaciones
                if not found_type:
                    # Buscar nodos que referencien a este foco y tengan un tipo conocido
                    for s, p, o in original_graph.triples((None, None, focus_uri)):
                        for _, _, type_uri in original_graph.triples((s, RDF_TYPE, None)):
                            if type_uri == DCAT.Dataset:
                                entity_type = "Dataset"
                                found_type = True
                                break
                            elif type_uri == DCAT.Catalog:
                                entity_type = "Catalog"
                                found_type = True
                                break
                            elif type_uri == DCAT.Distribution:
                                entity_type = "Distribution"
                                found_type = True
                                break
                            elif type_uri == DCAT.DataService:
                                entity_type = "DataService"
                                found_type = True
                                break
                        
                        if found_type:
                            break
                            
                # Si aún no tenemos tipo, buscar por propiedades características
                if not found_type:
                    # Dataset
                    if any(original_graph.triples((focus_uri, DCT.title, None))) and any(original_graph.triples((focus_uri, DCT.description, None))):
                        entity_type = "Dataset"
                    # Distribution
                    elif any(original_graph.triples((focus_uri, DCAT.downloadURL, None))) or any(original_graph.triples((focus_uri, DCAT.accessURL, None))):
                        entity_type = "Distribution"
                    # Catalog
                    elif any(original_graph.triples((focus_uri, DCAT.dataset, None))):
                        entity_type = "Catalog"
            except Exception as e:
                # Si hay un error, simplemente continuar con el tipo desconocido
                print(f"Error al detectar tipo de entidad para {focus_node}: {e}")
                pass
        
        result_info = {
            "message": message,
            "focus_node": focus_node,  # Mantener la URI completa
            "path": result_path,       # Mantener el path completo
            "severity": severity,
            "value": value,            # Incluir el valor problemático
            "entity_type": entity_type # Añadir tipo de entidad
        }
        
        # Clasificar según severidad
        if severity == "Violation":
            violations.append(result_info)
        elif severity == "Warning":
            warnings.append(result_info)
    
    return {
        "conforms": conforms,
        "violations": violations,
        "warnings": warnings,
        "violations_count": len(violations),
        "warnings_count": len(warnings)
    }

def parse_with_regex(report_content):
    """
    Utiliza expresiones regulares para analizar el informe SHACL.
    Este método es un fallback si rdflib no está disponible o falla.
    """
    conforms = "sh:conforms  true" in report_content or "Conforms: true" in report_content
    
    # Extraer resultados con regex
    violations = []
    warnings = []
    
    # Buscar todos los bloques de resultados
    result_blocks = re.findall(r'sh:result\s+\[\s+rdf:type\s+sh:ValidationResult[^]]*\]', report_content)
    
    for block in result_blocks:
        # Extraer información
        message = re.search(r'sh:resultMessage\s+"([^"]*)"', block)
        message = message.group(1) if message else "Sin mensaje"
        
        focus_node = re.search(r'sh:focusNode\s+<([^>]*)>', block)
        focus_node = focus_node.group(1) if focus_node else "Desconocido"
        
        # Capturar el path completo incluyendo prefijos
        path = re.search(r'sh:resultPath\s+(\S+)', block)
        path_value = path.group(1) if path else None
        
        # Extraer valor que causa la violación (puede ser URI o literal)
        value = None
        value_uri = re.search(r'sh:value\s+<([^>]*)>', block)
        value_literal = re.search(r'sh:value\s+"([^"]*)"', block)
        if value_uri:
            value = value_uri.group(1)
        elif value_literal:
            value = value_literal.group(1)
        
        severity = "Warning" if "sh:Warning" in block else "Violation"
        
        # Inferir tipo de entidad basado en patrones en la URI del focus_node
        entity_type = "Desconocido"
        if focus_node and focus_node != "Desconocido":
            # Intentar adivinar el tipo basado en patrones comunes
            if "/dataset/" in focus_node.lower() or "dataset" in focus_node.lower():
                entity_type = "Dataset"
            elif "/distribution/" in focus_node.lower() or "distribution" in focus_node.lower():
                entity_type = "Distribution"
            elif "/catalog/" in focus_node.lower() or "catalog" in focus_node.lower():
                entity_type = "Catalog"
            elif "/dataservice/" in focus_node.lower() or "service" in focus_node.lower():
                entity_type = "DataService"
        
        result_info = {
            "message": message,
            "focus_node": focus_node,  # URI completa
            "path": path_value,        # Path completo con prefijo
            "severity": severity,
            "value": value,            # Incluir el valor problemático
            "entity_type": entity_type # Intentar detectar tipo
        }
        
        if severity == "Violation":
            violations.append(result_info)
        else:
            warnings.append(result_info)
            
    return {
        "conforms": conforms,
        "violations": violations,
        "warnings": warnings,
        "violations_count": len(violations),
        "warnings_count": len(warnings)
    }

def get_shacl_results_dataframes(validation_details, profile_name=None, profile_version=None):
    """
    Convierte los resultados de validación SHACL en DataFrames para mostrarlos
    con tablas nativas de Streamlit.
    
    Args:
        validation_details: Detalles de validación obtenidos de parse_shacl_report
        profile_name: Nombre del perfil utilizado en la validación
        profile_version: Versión del perfil utilizado
        
    Returns:
        dict: DataFrames de pandas con los datos formateados
    """    
    # Función para convertir URI a prefijo:propiedad
    def format_property(uri):
        if not uri or uri == "N/A":
            return "N/A"
            
        # Convertir URI a formato prefijo:propiedad
        for namespace, prefix in PREFIXES.items():
            if uri.startswith(namespace):
                local_name = uri[len(namespace):]
                return f"{prefix}{local_name}"
                
        # Si no coincide con ningún prefijo conocido, devolver la URI original
        return uri

    # Función para añadir iconos a los tipos de entidad
    def add_entity_icon(entity_type):
        if entity_type == "Dataset":
            return "📊 Dataset"
        elif entity_type == "Catalog":
            return "📚 Catalog"
        elif entity_type == "Distribution":
            return "📄 Distribution"
        elif entity_type == "DataService":
            return "⚙️ DataService"
        elif entity_type == "CatalogRecord":
            return "📝 CatalogRecord"
        elif entity_type == "Agent":
            return "👤 Agent"
        elif entity_type == "Identifier":
            return "🔑 Identifier"
        elif entity_type == "Location":
            return "📍 Location"
        elif entity_type == "PeriodOfTime":
            return "⏱️ PeriodOfTime"
        elif entity_type == "Checksum":
            return "🔒 Checksum"
        elif entity_type == "Relationship":
            return "🔗 Relationship"
        else:
            return "❓ " + entity_type

    # Crear DataFrame para violaciones con iconos en los tipos
    violations_data = []
    for v in validation_details.get("violations", []):
        property_raw = v.get("path", "N/A")
        property_formatted = format_property(property_raw)
        entity_type = v.get("entity_type", "Desconocido")
        
        violations_data.append({
            "Tipo": entity_type,  # Tipo original para agrupación
            "TipoVisual": add_entity_icon(entity_type),  # Tipo con icono para visualización
            "Nodo": v.get("focus_node", ""),
            "Propiedad": property_formatted,
            "PropiedadOriginal": property_raw,
            "Valor": v.get("value", ""),
            "Mensaje": v.get("message", ""),
            "DocLink": create_doc_link(property_formatted, profile_name, profile_version)
        })
    
    # Crear DataFrame para advertencias
    warnings_data = []
    for w in validation_details.get("warnings", []):
        property_raw = w.get("path", "N/A")
        property_formatted = format_property(property_raw)
        
        warnings_data.append({
            "Tipo": w.get("entity_type", "Desconocido"),  # Añadir tipo de entidad
            "Nodo": w.get("focus_node", ""),
            "Propiedad": property_formatted,
            "PropiedadOriginal": property_raw,  # Guardar la propiedad original para el agrupamiento
            "Valor": w.get("value", ""),
            "Recomendación": w.get("message", ""),
            "DocLink": create_doc_link(property_formatted, profile_name, profile_version)
        })
    
    # Convertir a DataFrames
    violations_df = pd.DataFrame(violations_data) if violations_data else None
    warnings_df = pd.DataFrame(warnings_data) if warnings_data else None
    
    # Crear resúmenes por tipo y propiedad
    violations_by_type_property = None
    if violations_df is not None and not violations_df.empty:
        # Agrupamiento por tipo y propiedad
        violations_by_type_property = violations_df.groupby(["Tipo", "Propiedad"]).size().reset_index(name="Cantidad")
        violations_by_type_property = violations_by_type_property.sort_values(["Tipo", "Cantidad"], ascending=[True, False])
        
        # Añadir enlaces a la documentación
        violations_by_type_property["DocLink"] = violations_by_type_property["Propiedad"].apply(
            lambda p: create_doc_link(p, profile_name, profile_version)
        )
    
    # También crear resúmenes simples por propiedad (para mantener compatibilidad)
    violations_by_property = None
    if violations_df is not None and not violations_df.empty:
        violations_by_property = violations_df.groupby("Propiedad").size().reset_index(name="Cantidad")
        violations_by_property = violations_by_property.sort_values("Cantidad", ascending=False)
        
        # Añadir enlaces a la documentación
        violations_by_property["DocLink"] = violations_by_property["Propiedad"].apply(
            lambda p: create_doc_link(p, profile_name, profile_version)
        )
    
    # Igual para advertencias
    warnings_by_type_property = None
    if warnings_df is not None and not warnings_df.empty:
        # Agrupamiento por tipo y propiedad
        warnings_by_type_property = warnings_df.groupby(["Tipo", "Propiedad"]).size().reset_index(name="Cantidad")
        warnings_by_type_property = warnings_by_type_property.sort_values(["Tipo", "Cantidad"], ascending=[True, False])
        
        # Añadir enlaces a la documentación
        warnings_by_type_property["DocLink"] = warnings_by_type_property["Propiedad"].apply(
            lambda p: create_doc_link(p, profile_name, profile_version)
        )
    
    warnings_by_property = None
    if warnings_df is not None and not warnings_df.empty:
        warnings_by_property = warnings_df.groupby("Propiedad").size().reset_index(name="Cantidad")
        warnings_by_property = warnings_by_property.sort_values("Cantidad", ascending=False)
        
        # Añadir enlaces a la documentación
        warnings_by_property["DocLink"] = warnings_by_property["Propiedad"].apply(
            lambda p: create_doc_link(p, profile_name, profile_version)
        )
    
    # Devolver todos los DataFrames y estadísticas en un diccionario
    return {
        "violations": violations_df,
        "warnings": warnings_df,
        "violations_by_property": violations_by_property,
        "warnings_by_property": warnings_by_property,
        "violations_by_type_property": violations_by_type_property,
        "warnings_by_type_property": warnings_by_type_property,
        "violations_count": len(violations_data),
        "warnings_count": len(warnings_data)
    }
    
def create_doc_link(property_with_prefix, profile_name=None, profile_version=None):
    """
    Genera dinámicamente enlaces a la documentación según el perfil seleccionado.
    Utiliza la configuración de documentación en PROFILES.
    
    Args:
        property_with_prefix: Propiedad en formato 'prefijo:nombre'
        profile_name: Nombre del perfil (e.j., 'DCAT-AP-ES', 'DCAT-AP')
        profile_version: Versión del perfil (e.j., '1.0.0', '3.0.0')
        
    Returns:
        str: URL a la documentación o None
    """
    if property_with_prefix == "N/A" or ":" not in property_with_prefix:
        return None
    
    # Usar por defecto DCAT-AP-ES si no se especifica
    profile_name = profile_name or "DCAT-AP-ES"
    
    try:
        # Extraer prefijo y nombre de propiedad
        prefix, prop = property_with_prefix.split(":")
        prefix = prefix.rstrip(":")
        prop = prop.lower()  # Normalizar a minúsculas
        
        # Obtener configuración de documentación para el perfil
        doc_config = {}
        
        # Si el perfil existe en la configuración
        if profile_name not in PROFILES:
            return None
            
        profile_config = PROFILES[profile_name]
        
        # Obtener configuración a nivel de perfil general
        if "documentation" in profile_config:
            doc_config.update(profile_config["documentation"])
            
        # Si hay versión específica, buscar configuración para esa versión
        if profile_version and profile_version in profile_config:
            version_config = profile_config[profile_version]
            # Si hay documentación específica para esta versión
            if "documentation" in version_config:
                doc_config.update(version_config["documentation"])
        
        # Verificar si tenemos la configuración necesaria
        if not doc_config or "doc_base_url" not in doc_config:
            return None
            
        # Verificar si el prefijo está documentado
        if "documented_prefixes" in doc_config and prefix.lower() not in doc_config["documented_prefixes"]:
            return None
        
        # Obtener configuración necesaria
        base_url = doc_config.get("doc_base_url")
        if not base_url:
            return None
        
        # ---- MÉTODO 1: Usar patrones de URL específicos por entidad ----
        url_patterns = doc_config.get("url_patterns", {})
        if url_patterns:
            # Intentar formar URL para cada tipo de entidad en url_patterns
            for entity, pattern in url_patterns.items():
                url_fragment = pattern.format(
                    prefix=prefix.lower(),
                    property=prop
                )
                
                # Construir URL completa
                doc_url = f"{base_url.rstrip('/')}{url_fragment}"
                return doc_url  # Devolver la primera URL formada
        
        # ---- MÉTODO 2: Usar patrón genérico (para DCAT-AP) ----
        entity_property_pattern = doc_config.get("entity_property_pattern")
        if entity_property_pattern:
            # Para DCAT-AP, usamos directamente el EntityPascal.property
            # Por ejemplo: #Dataset.title
            entity_types = ["Dataset", "Catalog", "Distribution", "DataService"]
            for entity in entity_types:
                url_fragment = entity_property_pattern.format(
                    EntityPascal=entity,
                    property=prop
                )
                
                # Construir URL completa
                doc_url = f"{base_url.rstrip('/')}{url_fragment}"
                return doc_url  # Devolver la primera URL formada
        
        # Si llegamos aquí, no pudimos construir una URL
        return None
        
    except Exception as e:
        print(f"Error generando enlace para {property_with_prefix}: {e}")
    
    return None