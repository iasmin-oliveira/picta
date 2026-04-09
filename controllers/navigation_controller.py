"""
PICTA — controllers/navigation_controller.py
Roteador principal baseado em perfil autenticado.
"""

import streamlit as st
from views.painel_crianca import render as render_crianca
from views.dashboard_cuidador import render as render_dashboard
from controllers.auth_controller import is_authenticated, login, logout


def route_app() -> None:
    if not is_authenticated():
        login()
        return

    perfil = st.session_state.get('usuario', {}).get('perfil', '')

    if perfil == 'crianca':
        render_crianca()
    elif perfil == 'cuidador':
        render_dashboard()
    else:
        st.error("Perfil não reconhecido.")
        if st.button("↩️ Voltar ao login"):
            logout()
