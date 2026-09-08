"""
PICTA — controllers/auth_controller.py
Sessão persistente via cookie + banco de dados.
"""

import threading
import time
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components

from modules.auth import (
    autenticar_usuario,
    criar_sessao,
    renovar_sessao,
    revogar_sessao,
    solicitar_recuperacao_senha,
    trocar_senha_obrigatoria,
    validar_sessao,
)

COOKIE_NAME = "picta_session"
COOKIE_MAX_AGE = 30 * 60
SESSION_RENEW_INTERVAL_SECONDS = 60
COOKIE_ATTRIBUTES = "path=/; Secure; SameSite=Strict"


def _executar_sessao_em_background(nome: str, func, *args) -> None:
    def worker() -> None:
        try:
            func(*args)
        except Exception:
            pass
    threading.Thread(target=worker, name=nome, daemon=True).start()


def _ler_cookie() -> Optional[str]:
    try:
        return st.context.cookies.get(COOKIE_NAME)
    except Exception:
        return None


def _escrever_cookie_neste_render(token: str) -> None:
    components.html(
        f"<script>window.parent.document.cookie = "
        f"'{COOKIE_NAME}={token}; max-age={COOKIE_MAX_AGE}; {COOKIE_ATTRIBUTES}';</script>",
        height=1,
    )


def _apagar_cookie() -> None:
    components.html(
        f"<script>window.parent.document.cookie = "
        f"'{COOKIE_NAME}=; max-age=0; {COOKIE_ATTRIBUTES}';</script>",
        height=1,
    )


def processar_cookie_pendente() -> None:
    if st.session_state.pop("_pending_cookie_delete", False):
        _apagar_cookie()
        st.session_state["_sessao_verificada"] = True
        return
    token = st.session_state.pop("_pending_cookie", None)
    if token:
        _escrever_cookie_neste_render(token)


def _encerrar_sessao_local() -> None:
    st.session_state.clear()
    st.session_state["_pending_cookie_delete"] = True
    st.session_state["_sessao_verificada"] = True


def is_authenticated() -> bool:
    if st.session_state.get("autenticado"):
        token = st.session_state.get("token")
        agora = time.time()
        ultima = st.session_state.get("_ultima_verificacao_sessao", 0)
        if not token:
            _encerrar_sessao_local()
            return False
        if agora - ultima >= SESSION_RENEW_INTERVAL_SECONDS:
            usuario = validar_sessao(token)
            st.session_state["_ultima_verificacao_sessao"] = agora
            if not usuario:
                _encerrar_sessao_local()
                return False
            st.session_state["usuario"] = usuario
            _executar_sessao_em_background("picta-renovar-sessao", renovar_sessao, token)
        return True

    if st.session_state.get("_sessao_verificada"):
        return False
    st.session_state["_sessao_verificada"] = True
    token = _ler_cookie()
    if not token:
        return False
    usuario = validar_sessao(token)
    if usuario:
        st.session_state.update({
            "autenticado": True,
            "usuario": usuario,
            "token": token,
            "_pending_cookie": token,
            "_ultima_verificacao_sessao": time.time(),
        })
        return True
    _apagar_cookie()
    return False


def login() -> None:
    tela = st.session_state.get("tela", "login")
    if tela == "cadastro":
        from views.cadastro import render as render_cadastro
        render_cadastro()
        return

    from views.login import render_login_form
    (
        username, senha, submitted, feedback,
        reset_email, reset_submitted, reset_feedback,
    ) = render_login_form()

    if reset_submitted:
        erro_reset = solicitar_recuperacao_senha(reset_email)
        if erro_reset:
            reset_feedback.error("❌ " + erro_reset)
        else:
            reset_feedback.success("Se o email estiver cadastrado, enviaremos uma senha temporaria.")
        return

    if not submitted:
        return
    if not username.strip() or not senha:
        feedback.warning("Preencha usuário e senha para entrar.")
        return

    user = autenticar_usuario(username, senha)
    if not user:
        feedback.error("Usuário ou senha não conferem. Tente novamente.")
        return

    token = criar_sessao(user["id"])
    st.session_state.update({
        "autenticado": True,
        "usuario": user,
        "token": token,
        "_sessao_verificada": True,
        "_pending_cookie": token,
        "_ultima_verificacao_sessao": time.time(),
    })
    st.rerun()


def render_troca_senha_obrigatoria() -> None:
    from utils.css_loader import inject_css
    inject_css("picta_design.css")
    st.markdown(
        '<div style="max-width:520px;margin:2rem auto;">'
        '<div class="glass-card" style="padding:1.4rem 1.5rem;">'
        '<div class="sec-header">🔐 Troque sua senha</div>'
        '<div style="font-size:.9rem;color:#4b5563;font-weight:600;line-height:1.5">'
        'Voce entrou com uma senha temporaria. Crie uma nova senha para continuar.'
        '</div></div></div>',
        unsafe_allow_html=True,
    )
    usuario = st.session_state.get("usuario", {})
    with st.form("form_troca_senha_obrigatoria"):
        nova = st.text_input("Nova senha", type="password", placeholder="Minimo 6 caracteres")
        confirmar = st.text_input("Confirmar nova senha", type="password")
        submitted = st.form_submit_button("Salvar nova senha", use_container_width=True)
    if not submitted:
        return
    if nova != confirmar:
        st.error("As senhas nao coincidem.")
        return
    erro = trocar_senha_obrigatoria(usuario.get("id"), nova)
    if erro:
        st.error("❌ " + erro)
        return
    st.session_state["usuario"]["deve_trocar_senha"] = False
    st.success("Senha alterada com sucesso.")
    st.rerun()


def logout() -> None:
    token = st.session_state.get("token")
    if token:
        _executar_sessao_em_background("picta-revogar-sessao", revogar_sessao, token)
    _encerrar_sessao_local()
    st.rerun()
