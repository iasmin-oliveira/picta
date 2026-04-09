from typing import Optional, List
"""
PICTA — controllers/auth_controller.py
Fluxo de autenticação com sessão persistente via cookie.

Ciclo completo:
  - login()        → valida credenciais, gera token, salva cookie
  - is_authenticated() → tenta restaurar sessão do cookie se session_state vazio
  - logout()       → revoga token, apaga cookie, limpa state
"""

import streamlit as st
from modules.auth import autenticar_usuario, criar_sessao, validar_sessao, revogar_sessao
from views.login import render_login_form

COOKIE_NAME = "picta_session"


def _ler_cookie() -> Optional[str]:
    """Lê o token de sessão do cookie via st.query_params ou components."""
    # Streamlit não tem API nativa de cookies; usamos query_params como fallback
    # e o componente streamlit-cookies-controller para persistência real.
    try:
        from streamlit_cookies_controller import CookieController
        controller = CookieController()
        return controller.get(COOKIE_NAME)
    except Exception:
        return None


def _gravar_cookie(token: str):
    try:
        from streamlit_cookies_controller import CookieController
        controller = CookieController()
        controller.set(COOKIE_NAME, token, max_age=7 * 24 * 3600)
    except Exception:
        pass


def _apagar_cookie():
    try:
        from streamlit_cookies_controller import CookieController
        controller = CookieController()
        controller.remove(COOKIE_NAME)
    except Exception:
        pass


def is_authenticated() -> bool:
    """
    Retorna True se há sessão ativa.
    Tenta restaurar do cookie se session_state estiver vazio (ex: após refresh).
    """
    if st.session_state.get('autenticado'):
        return True

    # Tenta restaurar pelo cookie
    token = _ler_cookie()
    if token:
        usuario = validar_sessao(token)
        if usuario:
            st.session_state['autenticado'] = True
            st.session_state['usuario']     = usuario
            st.session_state['token']       = token
            return True
        else:
            # Token inválido/expirado — limpa o cookie
            _apagar_cookie()

    return False


def login() -> None:
    """Renderiza formulário de login e processa autenticação."""
    username, senha, submitted = render_login_form()

    if not submitted:
        return

    if not username.strip() or not senha:
        st.error("⚠️  Por favor, preencha todos os campos.")
        return

    user = autenticar_usuario(username, senha)
    if not user:
        st.error("❌  Utilizador ou senha incorretos. Tente novamente.")
        return

    # Gera token persistente
    token = criar_sessao(user['id'])

    st.session_state['autenticado'] = True
    st.session_state['usuario']     = user
    st.session_state['token']       = token

    _gravar_cookie(token)
    st.rerun()


def logout() -> None:
    """Encerra a sessão: revoga token, apaga cookie, limpa state."""
    token = st.session_state.get('token')
    revogar_sessao(token)
    _apagar_cookie()
    st.session_state.clear()
    st.rerun()
