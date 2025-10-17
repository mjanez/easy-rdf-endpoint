"""
Módulo para gestionar traducciones en la aplicación RDF Validator.
Proporciona funciones para traducir textos según el idioma seleccionado.
"""
import os
import gettext
import streamlit as st

# Directorio base donde se encuentran las traducciones
LOCALE_DIR = os.path.join(os.path.dirname(__file__), 'locales')

# Idiomas disponibles
LANGUAGES = {
    'es': 'Español',
    'en': 'English', 
}

def setup_i18n():
    """
    Configura el sistema de traducción con el idioma adecuado.
    El idioma se almacena en la sesión de Streamlit.
    """
    # Si no hay idioma seleccionado, usar el predeterminado (español)
    if 'language' not in st.session_state:
        st.session_state.language = 'es'
    
    try:
        lang = st.session_state.language
        locale_path = os.path.join(LOCALE_DIR, lang, 'LC_MESSAGES', 'messages.mo')
        
        if os.path.exists(locale_path):
            translator = gettext.translation('messages', LOCALE_DIR, languages=[lang])
            translator.install()
            return translator.gettext
        else:
            return lambda text: text 
    except Exception as e:
        print(f"Error al configurar las traducciones: {e}")
        return lambda text: text  

def get_translator():
    """Devuelve la función de traducción actual."""
    if 'translator' not in st.session_state:
        st.session_state.translator = setup_i18n()
    return st.session_state.translator

# Función de traducción principal
def _(text):
    """
    Traduce un texto según el idioma configurado.
    
    Args:
        text (str): Texto a traducir
        
    Returns:
        str: Texto traducido
    """
    translator = get_translator()
    return translator(text)

# Función para cambiar el idioma actual
def change_language(lang):
    """
    Cambia el idioma actual y reconfigura el traductor.
    
    Args:
        lang (str): Código de idioma ('es', 'en', etc.)
    """
    if lang in LANGUAGES:
        st.session_state.language = lang
        st.session_state.translator = setup_i18n()
        return True
    return False

# Crear un selector de idioma para la interfaz
def language_selector(location="sidebar"):
    """
    Crea un selector de idioma en la interfaz de Streamlit.
    
    Args:
        location (str): Dónde colocar el selector ('sidebar' o 'main')
    """
    if location == "sidebar":
        container = st.sidebar
    else:
        container = st
    
    # Selector de idioma
    selected_language = container.selectbox(
        _("Idioma / Language"),
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        index=list(LANGUAGES.keys()).index(st.session_state.language) if 'language' in st.session_state else 0,
        key="language_selector"
    )
    
    # Cambiar el idioma si ha cambiado la selección
    if 'language' not in st.session_state or selected_language != st.session_state.language:
        change_language(selected_language)
        st.rerun()