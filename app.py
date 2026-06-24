"""
PICTA — app.py
Ponto de entrada da aplicação Streamlit.
"""

import streamlit as st
from utils.debug_logger import log_debug
from controllers.navigation_controller import route_app
from controllers.auth_controller import processar_cookie_pendente

log_debug("=========== STREAMLIT RERUN ===========")
log_debug("APP INICIADO")

# Configuração da página (DEVE ser o primeiro comando Streamlit)
st.set_page_config(
    page_title="PICTA — Assistente de Comunicação",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': (
            "PICTA — Assistente de Comunicação e Expressão Emocional "
            "para Crianças Neurodiversas\n\nFACCAT · Sistemas de Informação · 2026"
        )
    }
)

# Escreve o cookie pendente ANTES do routing, para que o JS execute
# neste render (que vai completar sem st.rerun() adicional).
processar_cookie_pendente()

route_app()
