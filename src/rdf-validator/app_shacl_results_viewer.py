import os
import streamlit as st
import pandas as pd
from shacl_validator import get_shacl_results_dataframes

def update_violations_entity_filter():
    st.session_state.violations_entity_filter = st.session_state.get('violations_entity_filter_widget', [])

def update_violations_property_filter():
    st.session_state.violations_property_filter = st.session_state.get('violations_property_filter_widget', [])

def update_warnings_entity_filter():
    st.session_state.warnings_entity_filter = st.session_state.get('warnings_entity_filter_widget', [])

def update_warnings_property_filter():
    st.session_state.warnings_property_filter = st.session_state.get('warnings_property_filter_widget', [])

def display_shacl_results(profile, version, case=None, selected_entity_type=None):
    """
    Muestra los resultados de validación SHACL si están disponibles en session_state
    
    Args:
        profile: Nombre del perfil (DCAT-AP-ES, NTI-RISP, etc.)
        version: Versión del perfil
        case: Caso de validación
        selected_entity_type: Tipo de entidad seleccionada para validar
    """
    if not st.session_state.validation_result:
        return
        
    result = st.session_state.validation_result  # Usar el resultado almacenado
    
    # Mostrar toda la información del perfil
    if "profile_info" in st.session_state:
        st.subheader(f"Informe de validación SHACL: **{st.session_state.profile_info}**", divider=True)
    
    # Mostrar resultados según el nivel de conformidad
    conformance_level = result.get("conformance_level", "violations")
    
    if conformance_level == "full":
        st.success("✅ El RDF **cumple completamente** con el perfil SHACL")
    elif conformance_level == "warnings":
        st.warning("⚠️ El RDF **cumple con el perfil SHACL** pero tiene recomendaciones de mejora")
    else:
        st.error("❌ El RDF **no cumple con el perfil SHACL**")
                    
    # Crear cuatro pestañas con mejor organización
    tab1, tab2, tab3, tab4 = st.tabs(["Resumen", "Errores", "Advertencias", "Informe TTL"])                    
                   
    # Pestaña 1: Resumen
    with tab1:
        _display_summary_tab(result, profile, version)
    
    # Pestaña 2: Errores (tabla completa)
    with tab2:
        _display_violations_tab(result, profile, version)
    
    # Pestaña 3: Advertencias (tabla completa)
    with tab3:
        _display_warnings_tab(result, profile, version)
    
    # Pestaña 4: Informe TTL
    with tab4:
        _display_ttl_report_tab(result)

def _display_summary_tab(result, profile, version):
    """Muestra la pestaña de resumen con estadísticas"""
    if "validation_details" in result:
        # Obtener datos como DataFrames para tablas nativas
        dataframes = get_shacl_results_dataframes(
            result["validation_details"],
            profile_name=profile,
            profile_version=version
        )
        
        # Mostrar resumen general
        if dataframes["violations_count"] == 0 and dataframes["warnings_count"] == 0:
            st.success("✅ El documento RDF es totalmente conforme con el perfil SHACL")
        else:
            summary = []
            if dataframes["violations_count"] > 0:
                summary.append(f"❌ {dataframes['violations_count']} errores")
            if dataframes["warnings_count"] > 0:
                summary.append(f"⚠️ {dataframes['warnings_count']} advertencias")
                
            # Mostrar mensaje de resumen con el estilo adecuado
            summary_text = ", ".join(summary)
            if dataframes["violations_count"] > 0:
                st.error(f"Resultado: {summary_text}")
            elif dataframes["warnings_count"] > 0:
                st.warning(f"Resultado: {summary_text}")
                st.info("Estas advertencias son recomendaciones de mejora pero el documento es válido según el perfil SHACL.")
        
        # Mostrar resúmenes por propiedad en columnas
        if (dataframes["violations_by_type_property"] is not None or 
            dataframes["warnings_by_type_property"] is not None):
            st.subheader("Resumen por tipo de entidad y propiedad")
            
            # Verificar si hay errores y advertencias para determinar layout
            has_violations = dataframes["violations_by_type_property"] is not None and len(dataframes["violations_by_property"]) > 0
            has_warnings = dataframes["warnings_by_type_property"] is not None and len(dataframes["warnings_by_property"]) > 0
            
            # Decidir si usar columnas o no
            if has_violations and has_warnings:
                _display_violations_and_warnings_summary(dataframes)
            elif has_violations:
                _display_violations_summary(dataframes)
            elif has_warnings:
                _display_warnings_summary(dataframes)

def _display_violations_tab(result, profile, version):
    if "validation_details" in result:
        dataframes = get_shacl_results_dataframes(
            result["validation_details"],
            profile_name=profile,
            profile_version=version
        )
        
        if dataframes["violations"] is not None and not dataframes["violations"].empty:
            st.subheader("❌ Tabla completa de errores")
            
            # Formatear la columna de documentación si existe
            if "DocLink" in dataframes["violations"].columns:
                dataframes["violations"]["Documentación"] = dataframes["violations"].apply(
                    lambda row: f"{row['DocLink']}" if pd.notna(row['DocLink']) else "", 
                    axis=1
                )
                
                # Determinar las columnas a mostrar
                display_columns = ["Tipo", "Nodo", "Propiedad", "Valor", "Mensaje", "Documentación"]
                display_df = dataframes["violations"][display_columns]
            else:
                display_df = dataframes["violations"]
            
            # Añadir filtros para tipo de entidad y propiedades
            if not display_df.empty:
                # Crear dos columnas para los filtros
                filter_col1, filter_col2 = st.columns(2)
                
                with filter_col1:
                    # Filtro por tipo de entidad
                    all_entity_types = sorted(display_df["Tipo"].unique())
                    
                    # Filtrar valores por defecto que existen en las opciones actuales
                    default_entity_values = [v for v in st.session_state.violations_entity_filter if v in all_entity_types]
                    
                    st.multiselect(
                        "Filtrar por tipo de entidad",
                        options=all_entity_types,
                        default=default_entity_values,
                        help="Selecciona los tipos de entidad que quieres visualizar",
                        key="violations_entity_filter_widget",
                        on_change=update_violations_entity_filter
                    )

                with filter_col2:
                    # Filtro por propiedad
                    all_properties = sorted(display_df["Propiedad"].unique())
                    
                    # Filtrar valores por defecto que existen en las opciones actuales
                    default_property_values = [v for v in st.session_state.violations_property_filter if v in all_properties]
                    
                    st.multiselect(
                        "Filtrar por propiedad",
                        options=all_properties,
                        default=default_property_values,
                        help="Selecciona las propiedades que quieres visualizar",
                        key="violations_property_filter_widget",
                        on_change=update_violations_property_filter
                    )
                
                # Aplicar filtros
                filtered_df = display_df
                
                # Filtrar por tipo de entidad si se seleccionaron
                if st.session_state.violations_entity_filter:
                    # Asegurarse de solo filtrar valores que existen en las opciones actuales
                    valid_entity_filters = [f for f in st.session_state.violations_entity_filter if f in all_entity_types]
                    if valid_entity_filters:
                        filtered_df = filtered_df[filtered_df["Tipo"].isin(valid_entity_filters)]

                # Filtrar por propiedades si se seleccionaron
                if st.session_state.violations_property_filter:
                    # Asegurarse de solo filtrar valores que existen en las opciones actuales 
                    valid_property_filters = [f for f in st.session_state.violations_property_filter if f in all_properties]
                    if valid_property_filters:
                        filtered_df = filtered_df[filtered_df["Propiedad"].isin(valid_property_filters)]
                
                # Mostrar tabla con descarga
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    height=min(600, len(filtered_df) * 50 + 38),
                    column_config={
                        "Tipo": st.column_config.TextColumn(
                            "Tipo entidad",
                            width="small",
                            help="Tipo de entidad (Dataset, Catalog, Distribution, DataService)"
                        ),
                        "Nodo": st.column_config.TextColumn(
                            "Nodo",
                            width="medium",
                            help="URI del nodo con problema"
                        ),
                        "Propiedad": st.column_config.TextColumn(
                            "Propiedad",
                            width="small",
                            help="Propiedad del nodo que viola la restricción"
                        ),
                        "Valor": st.column_config.TextColumn(
                            "Valor",
                            width="medium",
                            help="Valor que causa la violación"
                        ),
                        "Mensaje": st.column_config.TextColumn(
                            "Mensaje de error",
                            width="large"
                        ),
                        "Documentación": st.column_config.LinkColumn(
                            "Ayuda",
                            width="small",
                            help="Enlace a la nota de uso del modelo"
                        )
                    }
                )
                
                # Botón para descargar la tabla filtrada en formato CSV
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Descargar tabla de errores (CSV)",
                    csv,
                    f"errores_{os.path.basename(st.session_state.file_path)}.csv",
                    "text/csv",
                    key='download-csv-violations'
                )
        else:
            st.success("✅ No se encontraron errores en el documento")
    else:
        st.warning("No hay datos detallados disponibles para mostrar")

def _display_warnings_tab(result, profile, version):
    if "validation_details" in result:
        dataframes = get_shacl_results_dataframes(
            result["validation_details"],
            profile_name=profile,
            profile_version=version
        )
        
        if dataframes["warnings"] is not None and not dataframes["warnings"].empty:
            st.subheader("⚠️ Tabla completa de advertencias")
            st.info("Las **advertencias indican posibles recomendaciones**, pero no impiden que el documento sea válido.")
            
            # Formatear la columna de documentación si existe
            if "DocLink" in dataframes["warnings"].columns:
                dataframes["warnings"]["Documentación"] = dataframes["warnings"].apply(
                    lambda row: f"{row['DocLink']}" if pd.notna(row['DocLink']) else "", 
                    axis=1
                )
                
                # Determinar las columnas a mostrar
                display_columns = ["Tipo", "Nodo", "Propiedad", "Valor", "Recomendación", "Documentación"]
                display_df = dataframes["warnings"][display_columns]
            else:
                display_df = dataframes["warnings"]
            
            # Añadir filtros para tipo de entidad y propiedades
            if not display_df.empty:
                # Crear dos columnas para los filtros
                filter_col1, filter_col2 = st.columns(2)

                with filter_col1:
                    # Filtro por tipo de entidad
                    all_entity_types = sorted(display_df["Tipo"].unique())
                    default_entity_values = [v for v in st.session_state.warnings_entity_filter if v in all_entity_types]

                    st.multiselect(
                        "Filtrar por tipo de entidad",
                        options=all_entity_types,
                        default=default_entity_values,
                        help="Selecciona los tipos de entidad que quieres visualizar",
                        key="warnings_entity_filter_widget",
                        on_change=update_warnings_entity_filter
                    )
                
                with filter_col2:
                    # Filtro por propiedad
                    all_properties = sorted(display_df["Propiedad"].unique())
                    default_property_values = [v for v in st.session_state.warnings_property_filter if v in all_properties]

                    st.multiselect(
                        "Filtrar por propiedad",
                        options=all_properties,
                        default=default_property_values,
                        help="Selecciona las propiedades que quieres visualizar",
                        key="warnings_property_filter_widget",
                        on_change=update_warnings_property_filter
                    )
                
                # Aplicar filtros
                filtered_df = display_df
                
                # Filtrar por tipo de entidad si se seleccionaron
                if st.session_state.warnings_entity_filter:
                    filtered_df = filtered_df[filtered_df["Tipo"].isin(st.session_state.warnings_entity_filter)]
                
                # Filtrar por propiedades si se seleccionaron
                if st.session_state.warnings_property_filter:
                    filtered_df = filtered_df[filtered_df["Propiedad"].isin(st.session_state.warnings_property_filter)]
                
                # Mostrar tabla con descarga
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    height=min(600, len(filtered_df) * 50 + 38),
                    column_config={
                        "Tipo": st.column_config.TextColumn(
                            "Tipo entidad",
                            width="small",
                            help="Tipo de entidad (Dataset, Catalog, Distribution, DataService, etc.)"
                        ),
                        "Nodo": st.column_config.TextColumn(
                            "Nodo",
                            width="medium",
                            help="URI del nodo con advertencia"
                        ),
                        "Propiedad": st.column_config.TextColumn(
                            "Propiedad",
                            width="small",
                            help="Propiedad del nodo relacionada con la advertencia"
                        ),
                        "Valor": st.column_config.TextColumn(
                            "Valor",
                            width="medium",
                            help="Valor relacionado con la advertencia"
                        ),
                        "Recomendación": st.column_config.TextColumn(
                            "Recomendación",
                            width="large"
                        ),
                        "Documentación": st.column_config.LinkColumn(
                            "Ayuda",
                            width="small",
                            help="Enlace a la nota de uso del modelo"
                        )
                    }
                )
                
                # Botón para descargar la tabla filtrada en formato CSV
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Descargar tabla de advertencias (CSV)",
                    csv,
                    f"advertencias_{os.path.basename(st.session_state.file_path)}.csv",
                    "text/csv",
                    key='download-csv-warnings'
                )
        else:
            st.success("✅ No se encontraron advertencias en el documento")
    else:
        st.warning("No hay datos detallados disponibles para mostrar")

def _display_ttl_report_tab(result):
    # Actualizar el nombre de la pestaña para reflejar el contenido
    st.subheader("Informe de validación SHACL (TTL)")
    
    # Verificar disponibilidad del informe
    report_content = None
    
    # Caso 1: Archivo físico en el servidor
    if "report_file" in result and result["report_file"] and os.path.exists(result["report_file"]):
        with open(result["report_file"], 'r', encoding='utf-8') as f:
            report_content = f.read()
    # Caso 2: Contenido del informe en memoria
    elif "report_content" in result and result["report_content"]:
        report_content = result["report_content"]
    # Caso 3: Salida estándar
    elif "stdout" in result and result["stdout"]:
        report_content = result["stdout"]
    
    if report_content:
        # Botón para descargar el informe TTL
        st.download_button(
            "Descargar informe completo TTL", 
            report_content, 
            f"validation_report_{os.path.basename(st.session_state.file_path)}.ttl",
            mime="text/turtle",
            help="Descarga el informe de validación SHACL en formato Turtle (TTL)"
        )
        
        # Mostrar el contenido del informe TTL
        st.text_area("Informe de validación TTL", report_content, height=600)
    else:
        st.warning("No se encontró el informe TTL de validación")

def _display_violations_and_warnings_summary(dataframes):
    """Muestra resumen de errores y advertencias en dos columnas"""
    # Hay tanto errores como advertencias, mostrar en dos columnas
    col1, col2 = st.columns(2)
    
    # Columna de errores
    with col1:
        if "DocLink" in dataframes["violations_by_type_property"].columns:
            # Formatear la columna DocLink para mostrar un ícono de enlace si hay URL
            dataframes["violations_by_type_property"]["Documentación"] = dataframes["violations_by_type_property"].apply(
                lambda row: f"{row['DocLink']}" if pd.notna(row['DocLink']) else "", 
                axis=1
            )

            # Gráfico resumen: Tomar solo las 10 primeras para el gráfico
            if len(dataframes["violations_by_property"]) > 0:
                top_violations = dataframes["violations_by_property"].head(10)
                st.caption("❌ Top 10 propiedades con más errores")
                st.bar_chart(
                    data=top_violations.set_index("Propiedad")["Cantidad"],
                    use_container_width=True,
                    height=300
                )
                
            st.caption("❌ Errores por tipo de entidad y propiedad")
            # Mostrar dataframe con la nueva columna
            st.dataframe(
                dataframes["violations_by_type_property"][["Tipo", "Propiedad", "Cantidad", "Documentación"]],
                use_container_width=True,
                height=min(250, len(dataframes["violations_by_property"]) * 35 + 38),
                column_config={
                    "Propiedad": st.column_config.TextColumn(
                        "Propiedad",
                        width="medium",
                        help="Propiedad del nodo que viola la restricción"
                    ),
                    "Cantidad": st.column_config.NumberColumn(
                        "Cantidad", 
                        width="small",
                        format="%d"
                    ),
                    "Documentación": st.column_config.LinkColumn(
                        "Ayuda",
                        width="small",
                        help="Enlace a la nota de uso del modelo"
                    )
                }
            )
        else:
            # Mostrar dataframe sin columna de documentación
            st.dataframe(
                dataframes["violations_by_property"],
                use_container_width=True,
                height=min(250, len(dataframes["violations_by_property"]) * 35 + 38)
            )
    
    # Columna de advertencias
    with col2:
        _display_warnings_summary_content(dataframes)

# Continúa con el resto de las funciones siguiendo el mismo patrón
def _display_violations_summary(dataframes):
    """Muestra solo el resumen de errores"""
    # Solo hay errores, mostrarlos en contenedor centrado
    if "DocLink" in dataframes["violations_by_type_property"].columns:
        # Formatear la columna DocLink
        dataframes["violations_by_type_property"]["Documentación"] = dataframes["violations_by_type_property"].apply(
            lambda row: f"{row['DocLink']}" if pd.notna(row['DocLink']) else "", 
            axis=1
        )

        # Gráfico resumen centrado
        st.caption("❌ Top propiedades con más errores")
        top_violations = dataframes["violations_by_property"].head(10)
        st.bar_chart(
            data=top_violations.set_index("Propiedad")["Cantidad"],
            use_container_width=True,
            height=300
        )
        
        st.caption("❌ Errores por tipo de entidad y propiedad")
        # Contenedor un poco más estrecho para que quede centrado
        container = st.container()
        with container:
            st.dataframe(
                dataframes["violations_by_type_property"][["Tipo", "Propiedad", "Cantidad", "Documentación"]],
                use_container_width=True,
                height=min(250, len(dataframes["violations_by_property"]) * 35 + 38),
                column_config={
                    "Propiedad": st.column_config.TextColumn(
                        "Propiedad",
                        width="medium",
                        help="Propiedad del nodo que viola la restricción"
                    ),
                    "Cantidad": st.column_config.NumberColumn(
                        "Cantidad", 
                        width="small",
                        format="%d"
                    ),
                    "Documentación": st.column_config.LinkColumn(
                        "Ayuda",
                        width="small",
                        help="Enlace a la nota de uso del modelo"
                    )
                }
            )
    else:
        # Mostrar dataframe sin columna de documentación
        st.dataframe(
            dataframes["violations_by_property"],
            use_container_width=True,
            height=min(250, len(dataframes["violations_by_property"]) * 35 + 38)
        )

def _display_warnings_summary_content(dataframes):
    """Muestra el contenido del resumen de advertencias (usado tanto en columnas como individual)"""
    if "DocLink" in dataframes["warnings_by_property"].columns:
        # Formatear la columna DocLink para mostrar un ícono de enlace si hay URL
        dataframes["warnings_by_property"]["Documentación"] = dataframes["warnings_by_property"].apply(
            lambda row: f"{row['DocLink']}" if pd.notna(row['DocLink']) else "", 
            axis=1
        )
        
        # Gráfico resumen: Tomar solo las 10 primeras para el gráfico
        if len(dataframes["warnings_by_property"]) > 0:
            top_warnings = dataframes["warnings_by_property"].head(10)
            st.caption("⚠️ Top 10 propiedades con más advertencias")
            st.bar_chart(
                data=top_warnings.set_index("Propiedad")["Cantidad"],
                use_container_width=True,
                height=300
            )

        st.caption("⚠️ Advertencias por propiedad")
        # Mostrar dataframe con la nueva columna
        st.dataframe(
            dataframes["warnings_by_property"][["Propiedad", "Cantidad", "Documentación"]],
            use_container_width=True,
            height=min(250, len(dataframes["warnings_by_property"]) * 35 + 38),
            column_config={
                "Propiedad": st.column_config.TextColumn(
                    "Propiedad",
                    width="medium",
                    help="Propiedad del nodo relacionada con la advertencia"
                ),
                "Cantidad": st.column_config.NumberColumn(
                    "Cantidad", 
                    width="small",
                    format="%d"
                ),
                "Documentación": st.column_config.LinkColumn(
                    "Ayuda",
                    width="small",
                    help="Enlace a la nota de uso del modelo"
                )
            }
        )
    else:
        # Mostrar dataframe sin columna de documentación
        st.dataframe(
            dataframes["warnings_by_property"],
            use_container_width=True,
            height=min(250, len(dataframes["warnings_by_property"]) * 35 + 38)
        )

def _display_warnings_summary(dataframes):
    """Muestra solo el resumen de advertencias"""
    # Solo hay advertencias, mostrarlas en contenedor centrado
    container = st.container()
    with container:
        _display_warnings_summary_content(dataframes)