"""
PICTA — controllers/auth_controller.py
Sessão persistente via cookie + banco de dados.

Padrão de escrita de cookie:
  st.rerun() aborta o render atual ANTES do JS do components.html executar.
  Solução: gravar o token em session_state['_pending_cookie'] e escrever o
  cookie no início do PRÓXIMO render (antes do routing), quando o render
  vai até o final e o JS consegue executar no browser.
"""

from typing import Optional
import time
import streamlit as st
import streamlit.components.v1 as components
from modules.auth import autenticar_usuario, criar_sessao, validar_sessao, renovar_sessao, revogar_sessao

COOKIE_NAME    = 'picta_session'
COOKIE_MAX_AGE = 30 * 60   # 30 minutos em segundos
SESSION_RENEW_INTERVAL_SECONDS = 60


# ── Leitura/escrita de cookie ─────────────────────────────────────────────────

def _ler_cookie() -> Optional[str]:
    """Lê o token do cookie HTTP (via st.context — disponível desde Streamlit 1.37)."""
    try:
        return st.context.cookies.get(COOKIE_NAME)
    except Exception:
        return None


def _escrever_cookie_neste_render(token: str) -> None:
    """
    Escreve o cookie via JS neste render.
    Só chamar quando o render vai COMPLETAR (sem st.rerun() depois).
    """
    components.html(
        f"<script>"
        f"  window.parent.document.cookie = "
        f"  '{COOKIE_NAME}={token}; max-age={COOKIE_MAX_AGE}; path=/; SameSite=Strict';"
        f"</script>",
        height=1,
    )


def _apagar_cookie() -> None:
    """Apaga o cookie via JS (max-age=0)."""
    components.html(
        f"<script>"
        f"  window.parent.document.cookie = "
        f"  '{COOKIE_NAME}=; max-age=0; path=/; SameSite=Strict';"
        f"</script>",
        height=1,
    )


# ── API pública ───────────────────────────────────────────────────────────────

def processar_cookie_pendente() -> None:
    """
    Chamado NO INÍCIO de cada render (em app.py, antes de route_app).
    Se há um cookie pendente de escrita, escreve agora — este render vai
    completar normalmente, então o JS vai executar no browser.
    """
    if st.session_state.pop('_pending_cookie_delete', False):
        _apagar_cookie()
        st.session_state['_sessao_verificada'] = True
        return

    token = st.session_state.pop('_pending_cookie', None)
    if token:
        _escrever_cookie_neste_render(token)


def is_authenticated() -> bool:
    """
    Verifica autenticação:
    1. session_state já tem → retorna True e renova inatividade no BD
    2. cookie no browser → valida token no BD → restaura session_state
    3. sem nenhum → False
    """
    if st.session_state.get('autenticado'):
        # Renova inatividade no banco de forma espaçada; evita um UPDATE a cada rerun.
        token = st.session_state.get('token')
        agora = time.time()
        ultima_renovacao = st.session_state.get('_ultima_renovacao_sessao', 0)
        if token and (agora - ultima_renovacao) >= SESSION_RENEW_INTERVAL_SECONDS:
            renovar_sessao(token)
            st.session_state['_ultima_renovacao_sessao'] = agora
        return True

    # Evita re-verificar o cookie múltiplas vezes no mesmo render cycle
    if st.session_state.get('_sessao_verificada'):
        return False
    st.session_state['_sessao_verificada'] = True

    token = _ler_cookie()
    if not token:
        return False

    usuario = validar_sessao(token)
    if usuario:
        st.session_state.update({
            'autenticado':       True,
            'usuario':           usuario,
            'token':             token,
            '_pending_cookie':   token,   # renova o cookie neste render
        })
        return True

    _apagar_cookie()
    return False


def login() -> None:
    """Renderiza o formulário de login e processa o submit."""
    tela = st.session_state.get('tela', 'login')
    if tela == 'cadastro':
        from views.cadastro import render as render_cadastro
        render_cadastro()
        return

    from views.login import render_login_form
    username, senha, submitted, feedback = render_login_form()

    if not submitted:
        return
    if not username.strip() or not senha:
        feedback.warning("Preencha usuário e senha para entrar.")
        return

    user = autenticar_usuario(username, senha)
    if not user:
        feedback.error("Usuário ou senha não conferem. Tente novamente.")
        return

    token = criar_sessao(user['id'])
    # Guarda o token para ser escrito como cookie NO PRÓXIMO render
    # (depois do st.rerun), quando o render vai até o final.
    st.session_state.update({
        'autenticado':       True,
        'usuario':           user,
        'token':             token,
        '_sessao_verificada': True,
        '_pending_cookie':   token,
        '_ultima_renovacao_sessao': time.time(),
    })
    st.rerun()


def logout() -> None:
    """Encerra a sessão, apaga o cookie e limpa o state."""
    token = st.session_state.get('token')
    if token:
        revogar_sessao(token)
    st.session_state.clear()
    st.session_state['_pending_cookie_delete'] = True
    st.session_state['_sessao_verificada'] = True
    st.rerun()
