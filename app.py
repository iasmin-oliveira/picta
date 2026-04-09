"""
PICTA — app.py
Ponto de entrada da aplicação Streamlit.
Responsável pela configuração global e pelo roteamento entre perfis.

Para correr:
    streamlit run app.py
"""

import streamlit as st
from database.db import inicializar_db
from controllers.navigation_controller import route_app

# ── Configuração da página (DEVE ser o primeiro comando Streamlit) ────────
st.set_page_config(
    page_title="PICTA — Assistente de Comunicação",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'About': "PICTA — Assistente de Comunicação e Expressão Emocional para Crianças Neurodiversas\n\nFACCAT · Sistemas de Informação · 2026"
    }
)

# ── Inicializa o banco de dados (idempotente) ─────────────────────────────
inicializar_db()

# ── Roteador principal ────────────────────────────────────────────────────
def main() -> None:
    route_app()


if __name__ == "__main__":
    main()
else:
    # Quando executado via `streamlit run app.py`
    main()
