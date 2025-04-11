"""
Gestor de perfiles SHACL para DCAT-AP y DCAT-AP-ES.
Proporciona funciones para detectar tipos de entidades y seleccionar perfiles.
"""
import os
from rdflib import Graph, Namespace, URIRef

# Importar utilidades
from utils import (
    get_available_profiles, 
    get_entity_types,
    get_shape_files,
    get_case_description,
    is_case_recommended,
    get_default_case
)
from config import (
    DCAT,
    DCT,
    FOAF,
    LOCN,
    RDF,
    SPDX,
    TIME,
    VCARD,
)

def detect_entity_types(rdf_file):
    """
    Detecta los tipos de entidad DCAT en un archivo RDF.
    
    Args:
        rdf_file: Ruta al archivo RDF
        
    Returns:
        dict: Tipos de entidad encontrados con sus URIs
    """
    entity_types = {
        "Catalog": [],
        "DataService": [],
        "Dataset": [],
        "Distribution": [],
        "CatalogRecord": [],
        "Agent": [],
        "Identifier": [],
        "Location": [],
        "PeriodOfTime": [],
        "Checksum": [],
        "Relationship": []
    }
    
    try:
        g = Graph()
        g.parse(rdf_file)
        
        # Detectar datasets
        for s in g.subjects(RDF.type, DCAT.Dataset):
            entity_types["Dataset"].append(str(s))
        
        # Detectar catálogos
        for s in g.subjects(RDF.type, DCAT.Catalog):
            entity_types["Catalog"].append(str(s))
        
        # Detectar servicios de datos
        for s in g.subjects(RDF.type, DCAT.DataService):
            entity_types["DataService"].append(str(s))
        
        # Detectar distribuciones
        for s in g.subjects(RDF.type, DCAT.Distribution):
            entity_types["Distribution"].append(str(s))
        
        # Detectar CatalogRecord
        for s in g.subjects(RDF.type, DCAT.CatalogRecord):
            entity_types["CatalogRecord"].append(str(s))
        
        # Detectar Agent (FOAF.Agent, DCT.Agent, VCARD.Organization, etc.)
        for agent_type in [FOAF.Agent, FOAF.Organization, FOAF.Person, DCT.Agent, 
                          VCARD.Organization, VCARD.Individual]:
            for s in g.subjects(RDF.type, agent_type):
                entity_types["Agent"].append(str(s))
        
        # Detectar Identifier
        for s in g.subjects(RDF.type, DCT.Identifier):
            entity_types["Identifier"].append(str(s))
        
        # Detectar Location
        for location_type in [DCT.Location, LOCN.Location]:
            for s in g.subjects(RDF.type, location_type):
                entity_types["Location"].append(str(s))
        
        # Detectar PeriodOfTime
        for s in g.subjects(RDF.type, DCT.PeriodOfTime):
            entity_types["PeriodOfTime"].append(str(s))
        # También verificar periodos de tiempo definidos con TIME
        for s in g.subjects(RDF.type, TIME.Interval):
            entity_types["PeriodOfTime"].append(str(s))
        
        # Detectar Checksum
        for s in g.subjects(RDF.type, SPDX.Checksum):
            entity_types["Checksum"].append(str(s))
        
        # Detectar Relationship
        for s in g.subjects(RDF.type, DCT.Relationship):
            entity_types["Relationship"].append(str(s))

        # Detectar nodos que tienen propiedades de PeriodOfTime (por ejemplo, startDate o endDate)
        # Esto es para capturar nodos en blanco que no tienen un rdf:type explícito
        for s, p, o in g.triples((None, DCAT.startDate, None)):
            if str(s) not in entity_types["PeriodOfTime"]:
                entity_types["PeriodOfTime"].append(str(s))
                
        for s, p, o in g.triples((None, DCAT.endDate, None)):
            if str(s) not in entity_types["PeriodOfTime"]:
                entity_types["PeriodOfTime"].append(str(s))

        # Eliminar tipos vacíos
        entity_types = {k: v for k, v in entity_types.items() if v}
        
    except Exception as e:
        print(f"Error al detectar tipos de entidad: {str(e)}")
    
    return entity_types

def get_profile_dropdown_options():
    """
    Obtiene opciones para dropdown de perfiles en la UI.
    
    Returns:
        dict: Opciones organizadas jerárquicamente
    """
    available_profiles = get_available_profiles()
    options = {}
    
    for profile, versions in available_profiles.items():
        for version, cases in versions.items():
            for case in cases:
                # Añadir indicador de recomendado si corresponde
                recommended = is_case_recommended(profile, version, case)
                label = f"{case} {'✓' if recommended else ''}"
                
                # Organizar por "Perfil (Versión)"
                profile_key = f"{profile} {version}"
                if profile_key not in options:
                    options[profile_key] = []
                
                options[profile_key].append({
                    "label": label,
                    "value": f"{profile}|{version}|{case}",
                    "description": get_case_description(profile, version, case),
                    "recommended": recommended
                })
    
    return options

def get_entity_type_dropdown_options(profile, version, case):
    """
    Obtiene opciones para dropdown de tipos de entidad en la UI.
    
    Returns:
        list: Opciones disponibles
    """
    entity_types = get_entity_types(profile, version, case)
    
    # Personalizar las etiquetas para una mejor experiencia de usuario
    options = []
    for entity_type in entity_types:
        label = entity_type
        if entity_type == "Todas":
            label = "Todas las entidades"
            
        options.append({"label": label, "value": entity_type})
    
    return options

def parse_profile_selection(selection):
    """
    Analiza la selección de perfil.
    
    Args:
        selection: String en formato "profile|version|case"
        
    Returns:
        tuple: (profile, version, case)
    """
    parts = selection.split('|')
    if len(parts) != 3:
        return None, None, None
    
    return parts[0], parts[1], parts[2]

def get_recommendation_message(profile, version, case):
    """
    Genera un mensaje de recomendación para el perfil seleccionado utilizando
    admonitions de Streamlit para mejor visualización.
    
    Args:
        profile (str): Perfil seleccionado
        version (str): Versión del perfil
        case (str): Caso de uso seleccionado
        
    Returns:
        str: Mensaje de recomendación formateado para Streamlit
    """
    description = get_case_description(profile, version, case)
    is_recommended = is_case_recommended(profile, version, case)
    
    # Mensaje base con descripción del caso
    message = f"### {case}\n\n{description}"
            
    # Admonition para caso recomendado
    if is_recommended:
        message += "\n\n> :star: **Este caso es recomendado para la mayoría de los escenarios de validación.**"
    else:
        default_case = get_default_case(profile, version)
        if default_case and default_case != case:
            # Admonition de información para sugerir el caso recomendado
            message += f"\n\n> :information_source: **Nota:** El caso recomendado para este perfil es: `{default_case}`"
    
        # Para DCAT-AP-ES dar información adicional sobre los tipos de entidad
    if profile == "DCAT-AP-ES":
        message += "\n\n> :information_source: Sí solo deseas validar un tipo específico, selecciónalo en el desplegable de tipo de entidad."
    
    return message