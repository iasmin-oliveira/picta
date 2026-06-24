"""
PICTA — controllers/navigation_controller.py
Roteador principal baseado no perfil autenticado.
"""

import streamlit as st
from controllers.auth_controller import is_authenticated, login, logout

PERFIS_CUIDADOR      = ('responsavel', 'cuidador')
PERFIS_PROFISSIONAL  = ('profissional',)


def route_app() -> None:
    if not is_authenticated():
        login()
        return

    perfil = st.session_state.get('usuario', {}).get('perfil', '')

    if perfil == 'crianca':
        from views.painel_crianca import render as render_crianca

        render_crianca()
    elif perfil in PERFIS_CUIDADOR:
        from views.dashboard_cuidador import render as render_dashboard_cuidador

        render_dashboard_cuidador()
    elif perfil in PERFIS_PROFISSIONAL:
        from views.dashboard_profissional import render as render_dashboard_profissional

        render_dashboard_profissional()
    else:
        st.error("Perfil não reconhecido: " + perfil)
        if st.button("↩️ Voltar ao login"):
            logout()
