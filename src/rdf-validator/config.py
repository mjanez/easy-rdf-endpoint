"""
Configuración para los perfiles de validación SHACL de DCAT-AP.
Define los perfiles disponibles, sus versiones, y los casos de validación.
"""
import os
from rdflib import Namespace

# Ruta base para los archivos SHACL (ajusta según tu entorno)
APP_DIR = "/app/data"
SHACL_DIR = f"{APP_DIR}/shacl"
LOGS_DIR = "/app/logs"
TEMP_DIR = "/app/temp"

# Directorio para ontologías locales
ONTOLOGIES_DIR = os.path.join(os.path.dirname(APP_DIR), "ontologies")

# Cache para gráfos combinados
SHAPES_CACHE = {}

# Namespaces para detección de tipos
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCT = Namespace("http://purl.org/dc/terms/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
LOCN = Namespace("http://www.w3.org/ns/locn#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDF_TYPE = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#").type
SPDX = Namespace("http://spdx.org/rdf/terms#")
TIME = Namespace("http://www.w3.org/2006/time#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")

# Definición de perfiles DCAT-AP
PROFILES = {
    # Perfil NTI-RISP
    "NTI-RISP": {
        "documentation": {
            "doc_base_url": "https://datosgobes.github.io/NTI-RISP/",
            "documented_prefixes": [
                "dcat", "dct", "dc", "foaf", 
                "rdfs", "skos", "time"
            ],
            # Mapeo para documentación
            "url_patterns": {
                "dataset": "#dataset-{prefix}_{property}",
                "catalog": "#catalog-{prefix}_{property}",
                "distribution": "#distribution-{prefix}_{property}"
            }
        },        
        "1.0.0": {
            # Configuración de caso de validación
            "cases": {
                "Validación Completa": {
                    "description": "Validación completa del modelo de metadatos NTI-RISP (2013) incluyendo todas las restricciones y vocabularios controlados.",
                    "entity_type_shapes": {
                        "Dataset": ["nti-risp_dataset_shape.ttl", "nti-risp_common_shapes.ttl", 
                                    "nti-risp_vocabularies_shape.ttl", "nti-risp_shacl_imports.ttl", 
                                    "nti-risp_shacl_mdr_imports.ttl"],
                        "Catalog": ["nti-risp_catalog_shape.ttl", "nti-risp_common_shapes.ttl", 
                                    "nti-risp_vocabularies_shape.ttl", "nti-risp_shacl_imports.ttl",
                                    "nti-risp_shacl_mdr_imports.ttl"],
                        "Distribution": ["nti-risp_distribution_shape.ttl", "nti-risp_common_shapes.ttl", 
                                        "nti-risp_vocabularies_shape.ttl", "nti-risp_shacl_imports.ttl",
                                        "nti-risp_shacl_mdr_imports.ttl"],
                        "Todas": ["nti-risp_dataset_shape.ttl", "nti-risp_catalog_shape.ttl", 
                                 "nti-risp_distribution_shape.ttl", "nti-risp_common_shapes.ttl", 
                                 "nti-risp_vocabularies_shape.ttl", "nti-risp_shacl_imports.ttl",
                                 "nti-risp_shacl_mdr_imports.ttl"]
                    },
                    "entity_types": ["Todas", "Catalog", "Dataset", "Distribution"],
                    "recommended": True
                }
            },
            "default_case": "Validación Completa"
        }
    },
    
    # Perfiles de DCAT-AP-ES
    "DCAT-AP-ES": {
        "documentation": {
            "doc_base_url": "https://datosgobes.github.io/DCAT-AP-ES/",
            "documented_prefixes": [
                "dcat", "dct", "dc", "adms", "foaf", 
                "schema", "skos", "vcard", "locn", "prov"
            ],
            # Mapeo directo para cada combinación de entidad y propiedad
            "url_patterns": {
                "dataset": "#nota-dcat_dataset-{prefix}_{property}",
                "catalog": "#nota-dcat_catalog-{prefix}_{property}",
                "distribution": "#nota-dcat_distribution-{prefix}_{property}",
                "dataservice": "#nota-dcat_dataservice-{prefix}_{property}"
            }
        },        
        "1.0.0": {
            # Configuración de casos simplificada
            "cases": {
                "Completo": {
                    "description": "Validación completa de DCAT-AP-ES incluyendo todas las restricciones y vocabularios controlados.",
                    "entity_type_shapes": {
                        "Dataset": ["shacl_dataset_shape.ttl", "shacl_common_shapes.ttl", 
                                    "shacl_mdr-vocabularies.shape.ttl"],
                        "DataService": ["shacl_dataservice_shape.ttl", "shacl_common_shapes.ttl", 
                                        "shacl_mdr-vocabularies.shape.ttl"],
                        "Catalog": ["shacl_catalog_shape.ttl", "shacl_common_shapes.ttl", 
                                    "shacl_mdr-vocabularies.shape.ttl"],
                        "Distribution": ["shacl_distribution_shape.ttl", "shacl_common_shapes.ttl", 
                                        "shacl_mdr-vocabularies.shape.ttl"],
                        "Todas": ["shacl_dataset_shape.ttl", "shacl_dataservice_shape.ttl", 
                                 "shacl_catalog_shape.ttl", "shacl_distribution_shape.ttl", 
                                 "shacl_common_shapes.ttl", "shacl_mdr-vocabularies.shape.ttl"]
                    },
                    "entity_types": ["Todas", "Catalog", "DataService", "Dataset", "Distribution"]
                },
                "Completo con HVD": {
                    "description": "Validación completa de DCAT-AP-ES incluyendo todas las restricciones y vocabularios controlados, además de los requisitos para HVD (Datos de Alto Valor).",
                    "entity_type_shapes": {
                        "Dataset": ["shacl_dataset_shape.ttl", "shacl_common_shapes.ttl", 
                                    "shacl_dataset_hvd_shape.ttl", "shacl_common_hvd_shapes.ttl", 
                                    "shacl_mdr-vocabularies.shape.ttl"],
                        "DataService": ["shacl_dataservice_shape.ttl", "shacl_common_shapes.ttl", 
                                       "shacl_dataservice_hvd_shape.ttl", "shacl_common_hvd_shapes.ttl", 
                                       "shacl_mdr-vocabularies.shape.ttl"],
                        "Catalog": ["shacl_catalog_shape.ttl", "shacl_common_shapes.ttl", 
                                    "shacl_common_hvd_shapes.ttl", "shacl_mdr-vocabularies.shape.ttl"],
                        "Distribution": ["shacl_distribution_shape.ttl", "shacl_common_shapes.ttl", 
                                        "shacl_distribution_hvd_shape.ttl", "shacl_common_hvd_shapes.ttl", 
                                        "shacl_mdr-vocabularies.shape.ttl"],
                        "Todas": ["shacl_dataset_shape.ttl", "shacl_dataservice_shape.ttl", 
                                  "shacl_catalog_shape.ttl", "shacl_distribution_shape.ttl", 
                                  "shacl_common_shapes.ttl", "shacl_dataset_hvd_shape.ttl", 
                                  "shacl_dataservice_hvd_shape.ttl", "shacl_distribution_hvd_shape.ttl", 
                                  "shacl_common_hvd_shapes.ttl", "shacl_mdr-vocabularies.shape.ttl"]
                    },
                    "entity_types": ["Todas", "Catalog", "DataService", "Dataset", "Distribution"],
                    "recommended": True
                }
            },
            "default_case": "Completo con HVD"
        }
    },
    
    # Perfiles de DCAT-AP genérico
    "DCAT-AP": {
        "documentation": {
            "documented_prefixes": [
                "dcat", "dct", "dc", "adms", "foaf", 
                "schema", "skos", "vcard", "locn", "prov"
            ]
        },
        "2.1.1": {
            "documentation": {
                "doc_base_url": "https://semiceu.github.io/DCAT-AP/releases/2.1.1/",
                # Patrón simple para DCAT-AP que usa notación diferente
                "entity_property_pattern": "#{EntityPascal}.{property}"
            },
            "cases": {
                "Caso 1: Base Zero (sin conocimiento base)": {
                    "description": "Incluye todas las restricciones requeridas para la coherencia técnica, excluyendo las restricciones de pertenencia a clases de rango y uso de vocabularios controlados.",
                    "shapes": ["dcat-ap_2.1.1_shacl_shapes.ttl"],
                    "entity_types": ["Catalog", "DataService", "Dataset", "Distribution"]
                },
                "Caso 2: Ranges Zero (sin conocimiento base)": {
                    "description": "Incluye todas las restricciones de pertenencia a clases de rango.",
                    "shapes": ["dcat-ap_2.1.1_shacl_range.ttl"],
                    "entity_types": ["Catalog", "DataService", "Dataset", "Distribution"]
                },
                "Caso 3: Base (con conocimiento base)": {
                    "description": "Extiende el Caso 1 con conocimiento base, incluyendo todos los vocabularios utilizados en DCAT-AP.",
                    "shapes": ["dcat-ap_2.1.1_shacl_shapes.ttl", "dcat-ap_2.1.1_shacl_imports.ttl"],
                    "entity_types": ["Catalog", "DataService", "Dataset", "Distribution"],
                    "recommended": True
                },
                "Caso 4: Ranges (con conocimiento base)": {
                    "description": "Extiende el Caso 2 con conocimiento base, añadiendo validación de pertenencia a clases de rango y cumplimiento de estándares de vocabulario.",
                    "shapes": ["dcat-ap_2.1.1_shacl_range.ttl", "dcat-ap_2.1.1_shacl_imports.ttl"],
                    "entity_types": ["Catalog", "DataService", "Dataset", "Distribution"]
                },
                "Caso 5: Recomendaciones (con conocimiento base)": {
                    "description": "Incluye todas las restricciones relacionadas con propiedades recomendadas.",
                    "shapes": ["dcat-ap_2.1.1_shacl_shapes_recommended.ttl", "dcat-ap_2.1.1_shacl_imports.ttl"],
                    "entity_types": ["Catalog", "DataService", "Dataset", "Distribution"]
                },
                "Caso 6: Vocabularios Controlados": {
                    "description": "Incluye todas las restricciones relacionadas con vocabularios controlados.",
                    "shapes": ["dcat-ap_2.1.1_shacl_mdr-vocabularies.shape.ttl", "dcat-ap_2.1.1_shacl_mdr_imports.ttl"],
                    "entity_types": ["Catalog", "DataService", "Dataset", "Distribution"]
                },
                "Caso 7: Completo (con conocimiento base)": {
                    "description": "La unión de los Casos 3, 4, 5 y 6.",
                    "shapes": [
                        "dcat-ap_2.1.1_shacl_shapes.ttl", 
                        "dcat-ap_2.1.1_shacl_shapes_recommended.ttl", 
                        "dcat-ap_2.1.1_shacl_imports.ttl", 
                        "dcat-ap_2.1.1_shacl_range.ttl", 
                        "dcat-ap_2.1.1_shacl_deprecateduris.ttl",
                        "dcat-ap_2.1.1_shacl_mdr-vocabularies.shape.ttl", 
                        "dcat-ap_2.1.1_shacl_mdr_imports.ttl"
                    ],
                    "entity_types": ["Catalog", "DataService", "Dataset", "Distribution"]
                }
            },
            "default_case": "Caso 3: Base (con conocimiento base)"
        },
        "3.0.0": {
            "documentation": {
                "doc_base_url": "https://semiceu.github.io/DCAT-AP/releases/3.0.0/",
                # Patrón simple para DCAT-AP que usa notación diferente
                "entity_property_pattern": "#{EntityPascal}.{property}"
            },
            "cases": {
                "Caso 1: Base Zero (sin conocimiento base)": {
                    "description": "Incluye todas las restricciones requeridas para la coherencia técnica, excluyendo las restricciones de pertenencia a clases de rango y uso de vocabularios controlados.",
                    "shapes": ["dcat-ap_3.0.0_shacl_shapes.ttl"],
                    "entity_types": ["Catalog", "DataService", "Dataset", "Distribution"]
                },
                "Caso 2: Ranges Zero (sin conocimiento base)": {
                    "description": "Incluye todas las restricciones de pertenencia a clases de rango.",
                    "shapes": ["dcat-ap_3.0.0_shacl_range.ttl"],
                    "entity_types": ["Catalog", "DataService", "Dataset", "Distribution"]
                },
                "Caso 3: Base (con conocimiento base)": {
                    "description": "Extiende el Caso 1 con conocimiento base, incluyendo todos los vocabularios utilizados en DCAT-AP.",
                    "shapes": ["dcat-ap_3.0.0_shacl_shapes.ttl", "dcat-ap_3.0.0_shacl_imports.ttl"],
                    "entity_types": ["Catalog", "DataService", "Dataset", "Distribution"],
                    "recommended": True
                },
                "Caso 4: Ranges (con conocimiento base)": {
                    "description": "Extiende el Caso 2 con conocimiento base, añadiendo validación de pertenencia a clases de rango y cumplimiento de estándares de vocabulario.",
                    "shapes": ["dcat-ap_3.0.0_shacl_range.ttl", "dcat-ap_3.0.0_shacl_imports.ttl"],
                    "entity_types": ["Catalog", "DataService", "Dataset", "Distribution"]
                },
                "Caso 5: Recomendaciones (con conocimiento base)": {
                    "description": "Incluye todas las restricciones relacionadas con propiedades recomendadas.",
                    "shapes": ["dcat-ap_3.0.0_shacl_shapes_recommended.ttl", "dcat-ap_3.0.0_shacl_imports.ttl"],
                    "entity_types": ["Catalog", "DataService", "Dataset", "Distribution"]
                },
                "Caso 6: Vocabularios Controlados": {
                    "description": "Incluye todas las restricciones relacionadas con vocabularios controlados.",
                    "shapes": ["dcat-ap_3.0.0_shacl_mdr-vocabularies.shape.ttl", "dcat-ap_3.0.0_shacl_mdr_imports.ttl"],
                    "entity_types": ["Catalog", "DataService", "Dataset", "Distribution"]
                },
                "Caso 7: Completo (con conocimiento base)": {
                    "description": "La unión de los Casos 3, 4, 5 y 6.",
                    "shapes": [
                        "dcat-ap_3.0.0_shacl_shapes.ttl", 
                        "dcat-ap_3.0.0_shacl_shapes_recommended.ttl", 
                        "dcat-ap_3.0.0_shacl_imports.ttl", 
                        "dcat-ap_3.0.0_shacl_range.ttl", 
                        "dcat-ap_3.0.0_shacl_deprecateduris.ttl",
                        "dcat-ap_3.0.0_shacl_mdr-vocabularies.shape.ttl", 
                        "dcat-ap_3.0.0_shacl_mdr_imports.ttl"
                    ],
                    "entity_types": ["Catalog", "DataService", "Dataset", "Distribution"]
                }
            },
            "default_case": "Caso 3: Base (con conocimiento base)"
        }
    }
}

# Mapeo de namespaces a prefijos comunes
PREFIXES = {
    "http://www.w3.org/ns/adms#": "adms:",
    "http://datos.gob.es/recurso/sector-publico/org/Organismo/": "dir3:",
    "http://www.w3.org/ns/dcat#": "dcat:",
    "http://data.europa.eu/r5r/": "dcatap:",
    "http://purl.org/dc/elements/1.1/": "dc:",
    "http://purl.org/dc/terms/": "dct:",
    "http://purl.org/dc/dcmitype/": "dctype:",
    "http://publications.europa.eu/resource/authority/": "eu-authority:",
    "http://xmlns.com/foaf/0.1/": "foaf:",
    "http://data.europa.eu/930/": "geodcatap:",
    "http://www.w3.org/ns/locn#": "locn:",
    "http://www.w3.org/ns/odrl/2/": "odrl:",
    "http://www.w3.org/ns/org#": "org:",
    "http://www.w3.org/2002/07/owl#": "owl:",
    "http://www.w3.org/ns/prov#": "prov:",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf:",
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs:",
    "http://schema.org/": "schema:",
    "http://datos.gob.es/kos/sector-publico/sector/": "sector:",
    "http://www.w3.org/2004/02/skos/core#": "skos:",
    "http://spdx.org/rdf/terms#": "spdx:",
    "http://www.w3.org/2006/time#": "time:",
    "http://www.w3.org/2006/vcard/ns#": "vcard:",
    "http://www.w3.org/2001/XMLSchema#": "xsd:",
    "http://www.w3.org/2011/content#": "content:",
    "http://www.w3.org/ns/dqv#": "dqv:",
    "http://purl.org/linked-data/sdmx/2009/attribute#": "sdmx-attribute:",
}

# Mapeo de URIs para redirección a ontologías locales
ONTOLOGY_MAPPINGS = {
    "https://schema.org/version/latest/schema.ttl": "schema.org.ttl",
    "http://purl.org/dc/terms/": "dc-terms.ttl",
    "http://dublincore.org/2020/01/20/dublin_core_terms.ttl": "dublin_core_terms.ttl",
    "https://www.w3.org/ns/dcat2.ttl": "dcat2.ttl",
    "http://xmlns.com/foaf/spec/index.rdf": "foaf.rdf",
    "https://www.w3.org/ns/locn.ttl": "locn.ttl", 
    "https://spdx.org/rdf/terms/spdx-ontology.owl.xml": "spdx-ontology.owl.xml",
    "http://publications.europa.eu/ontology/euvoc": "euvoc.ttl"
}