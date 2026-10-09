"""
PICTA — views/dashboard_cuidador/__init__.py
Ponto de entrada do dashboard do Responsável / Cuidador.
"""

import html
import streamlit as st

from modules.auth import obter_criancas_do_usuario
from utils.css_loader import inject_css

from ._constants import LABEL_PERFIL, NAV
from ._hoje import render_hoje
from ._historico import render_historico
from ._crianca import render_crianca
from ._vinculos import render_vinculos
from ._perfil import render_perfil

ORIENTACOES_CUIDADOR = {
    "hoje": (
        "Hoje",
        "Veja um resumo das comunicações mais recentes da criança selecionada. Esta tela ajuda a entender "
        "como foi o dia e quais necessidades, ações ou emoções apareceram.",
    ),
    "hist": (
        "Histórico",
        "Consulte as interações registradas em dias anteriores. Use os filtros para localizar períodos ou "
        "tipos de comunicação específicos.",
    ),
    "crianca": (
        "Minha criança",
        "Confira e edite os dados da criança vinculada. As informações daqui ajudam o PICTA a organizar "
        "o acompanhamento no painel do responsável.",
    ),
    "vinculos": (
        "Vínculos",
        "Use esta tela para vincular uma criança ao seu painel e convidar profissionais de saúde. O convite "
        "usa o nome de usuário cadastrado pelo profissional no PICTA.",
    ),
    "perfil": (
        "Meu perfil",
        "Atualize seus dados de acesso e senha. Se você cuida de uma criança, também pode alterar a senha "
        "dela nesta área quando houver vínculo ativo. Os formulários da pesquisa também ficam nesta tela.",
    ),
}


def render() -> None:
    inject_css('picta_design.css')

    usuario = st.session_state.get('usuario', {})
    nome = usuario.get('nome', '')
    usuario_id = usuario.get('id')
    perfil = usuario.get('perfil', '')
    primeiro = nome.split()[0] if nome else ''
    label = LABEL_PERFIL.get(perfil, 'Usuário')
    nome_html = html.escape(str(nome), quote=True)
    label_html = html.escape(str(label), quote=True)
    criancas = obter_criancas_do_usuario(usuario_id, perfil)

    with st.sidebar:
        st.markdown(
            '<div class="sidebar-logo">'
            '  <div class="sidebar-logo-icon">'
            '    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"'
            '      viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"'
            '      stroke-linecap="round" stroke-linejoin="round">'
            '      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'
            '    </svg></div>'
            '  <span class="sidebar-logo-text">PICTA</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        crianca_id, crianca_nome = None, ''
        if criancas:
            st.markdown('<div class="sidebar-select-label">Acompanhando</div>', unsafe_allow_html=True)
            nomes_por_id = {int(c['id']): str(c['nome']) for c in criancas}
            ids = list(nomes_por_id)
            sel_id = st.selectbox(
                "Criança",
                ids,
                format_func=lambda cid: nomes_por_id.get(int(cid), "Criança"),
                key="cui_sel_id",
                label_visibility="collapsed",
            )
            crianca_id = int(sel_id)
            crianca_nome = nomes_por_id.get(crianca_id, "")
            st.markdown(
                f'<div class="sidebar-current-child">{html.escape(crianca_nome, quote=True)}</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)

        if 'cui_pag' not in st.session_state:
            st.session_state['cui_pag'] = 'hoje'

        for chave, emoji, titulo, desc in NAV:
            ativo = st.session_state['cui_pag'] == chave
            if st.button(f"{emoji}  {titulo}", key=f"cui_nav_{chave}", use_container_width=True,
                         type="primary" if ativo else "secondary"):
                st.session_state['cui_pag'] = chave
                st.rerun()
            if ativo:
                st.markdown(f'<div class="nav-desc">{html.escape(str(desc), quote=True)}</div>', unsafe_allow_html=True)

        st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="sidebar-profile">'
            f'  <div class="sidebar-profile-top">'
            f'    <div class="sidebar-avatar-lg">👨‍👩‍👧</div>'
            f'    <div style="overflow:hidden">'
            f'      <div class="sidebar-profile-name">{nome_html}</div>'
            f'      <div class="sidebar-profile-role">{label_html}</div>'
            f'    </div></div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Encerrar Sessão", key="cui_logout", use_container_width=True):
            from controllers.auth_controller import logout
            logout()

    pag = st.session_state.get('cui_pag', 'hoje')
    _render_orientacao(pag)
    if pag == 'hoje':
        render_hoje(criancas, crianca_id, crianca_nome, primeiro)
    elif pag == 'hist':
        render_historico(criancas, crianca_id, crianca_nome)
    elif pag == 'crianca':
        render_crianca(usuario_id, criancas, crianca_id, crianca_nome)
    elif pag == 'vinculos':
        render_vinculos(usuario_id, perfil, criancas)
    elif pag == 'perfil':
        render_perfil(usuario_id, nome, primeiro, label)


def _render_orientacao(pag: str) -> None:
    titulo, texto = ORIENTACOES_CUIDADOR.get(pag, ORIENTACOES_CUIDADOR["hoje"])
    st.markdown(
        '<details class="dashboard-orientation-details">'
        '<summary>'
        '<span class="dashboard-orientation-open">&#9432; Orientações</span>'
        '<span class="dashboard-orientation-close" title="Fechar orientações">&times;</span>'
        '</summary>'
        '<div class="dashboard-orientation-body">'
        f'<div class="dashboard-orientation-title">{html.escape(titulo, quote=True)}</div>'
        f'<div class="dashboard-orientation-text">{html.escape(texto, quote=True)}</div>'
        '</div>'
        '</details>',
        unsafe_allow_html=True,
    )
