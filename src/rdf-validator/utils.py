import os

from config import SHACL_DIR, PROFILES

def get_profile_path(profile, version):
    """Obtiene la ruta completa a un perfil."""
    return os.path.join(SHACL_DIR, profile.lower(), version)

# Modificación en la función get_shape_files
def get_shape_files(profile, version, case, entity_type=None):
    """
    Obtiene los archivos de shape para un perfil, versión y caso específicos.
    
    Args:
        profile: Nombre del perfil (ej. "DCAT-AP", "DCAT-AP-ES", "NTI-RISP")
        version: Versión del perfil (ej. "2.1.1", "1.0.0")
        case: Nombre del caso de validación
        entity_type: Opcional, tipo de entidad específico para perfiles que soportan entity_type_shapes
        
    Returns:
        list: Lista de rutas completas a los archivos de shape que existen
    """
    if profile not in PROFILES or version not in PROFILES[profile]:
        print(f"Perfil {profile} versión {version} no encontrado en la configuración")
        return []
    
    profile_config = PROFILES[profile][version]
    case_config = profile_config["cases"].get(case)
    
    if not case_config:
        # Si el caso no existe, usar el caso predeterminado
        case = profile_config.get("default_case")
        case_config = profile_config["cases"].get(case)
        if not case_config:
            print(f"Caso predeterminado {case} no encontrado para {profile} {version}")
            return []
    
    base_path = get_profile_path(profile, version)
    found_files = []
    
    # Verificar que el directorio base exista
    if not os.path.exists(base_path):
        print(f"¡Error! Directorio de perfil no encontrado: {base_path}")
        print(f"SHACL_DIR configurado como: {SHACL_DIR}")
        return []
    
    # Para perfiles que usan entity_type_shapes (DCAT-AP-ES, NTI-RISP, etc.)
    if "entity_type_shapes" in case_config:
        # Si no se especificó un tipo de entidad o se seleccionó "Todas", usar la configuración para "Todas"
        if not entity_type or entity_type == "Todas":
            entity_type = "Todas"
        
        if entity_type not in case_config["entity_type_shapes"]:
            print(f"Tipo de entidad {entity_type} no válido para {profile} {version} {case}")
            return []
        
        shape_files = case_config["entity_type_shapes"][entity_type]
        for shape in shape_files:
            full_path = os.path.join(base_path, shape)
            if os.path.exists(full_path):
                found_files.append(full_path)
            else:
                print(f"⚠️ Archivo SHACL no encontrado: {full_path}")
    
    # Para perfiles que usan shapes directamente (DCAT-AP, etc.)
    else:
        shape_files = case_config.get("shapes", [])
        for shape in shape_files:
            full_path = os.path.join(base_path, shape)
            if os.path.exists(full_path):
                found_files.append(full_path)
            else:
                print(f"⚠️ Archivo SHACL no encontrado: {full_path}")
    
    # Agregar un mensaje informativo sobre el resultado
    if not found_files:
        print(f"No se encontraron archivos SHACL para {profile} {version} {case}")
        # Mostrar los archivos que se intentaron buscar
        if "entity_type_shapes" in case_config and entity_type:
            shapes_list = case_config["entity_type_shapes"].get(entity_type, [])
            print(f"Se intentaron cargar: {', '.join(shapes_list)}")
        elif "shapes" in case_config:
            print(f"Se intentaron cargar: {', '.join(case_config['shapes'])}")
    
    return found_files

def get_available_profiles():
    """
    Devuelve un diccionario con los perfiles disponibles.
    
    Returns:
        dict: Diccionario con perfiles, versiones y casos disponibles
    """
    available = {}
    
    for profile, profile_config in PROFILES.items():
        if profile not in available:
            available[profile] = {}
        
        for version_key, version_value in profile_config.items():
            # Ignorar entradas que no sean versiones (como "documentation")
            if version_key == "documentation" or not isinstance(version_value, dict):
                continue
                
            # Solo procesar si hay casos de validación disponibles
            if "cases" in version_value:
                available[profile][version_key] = list(version_value["cases"].keys())
    
    return available

def get_entity_types(profile, version, case):
    """
    Obtiene los tipos de entidad disponibles para un perfil, versión y caso.
    
    Returns:
        list: Lista de tipos de entidad
    """
    if (profile not in PROFILES or 
        version not in PROFILES[profile] or 
        case not in PROFILES[profile][version]["cases"]):
        return []
    
    return PROFILES[profile][version]["cases"][case]["entity_types"]

def get_case_description(profile, version, case):
    """
    Obtiene la descripción de un caso de validación.
    
    Returns:
        str: Descripción del caso
    """
    if (profile not in PROFILES or 
        version not in PROFILES[profile] or 
        case not in PROFILES[profile][version]["cases"]):
        return ""
    
    return PROFILES[profile][version]["cases"][case]["description"]

def is_case_recommended(profile, version, case):
    """
    Comprueba si un caso es recomendado.
    
    Returns:
        bool: True si el caso es recomendado
    """
    if (profile not in PROFILES or 
        version not in PROFILES[profile] or 
        case not in PROFILES[profile][version]["cases"]):
        return False
    
    return PROFILES[profile][version]["cases"][case].get("recommended", False)

def get_default_case(profile, version):
    """
    Obtiene el caso de validación predeterminado para un perfil y versión.
    
    Returns:
        str: Nombre del caso predeterminado
    """
    if profile not in PROFILES or version not in PROFILES[profile]:
        return None
    
    return PROFILES[profile][version].get("default_case")

