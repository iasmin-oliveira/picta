"""
PICTA — views/dashboard_cuidador/__init__.py
Ponto de entrada do dashboard do Responsável / Cuidador.

Estrutura do pacote:
    _constants.py  — constantes compartilhadas
    _hoje.py       — seção Hoje (~120 linhas)
    _historico.py  — seção Histórico (~80 linhas)
    _crianca.py    — seção Minha Criança (~110 linhas)
    _vinculos.py   — seção Vínculos (~80 linhas)
    _perfil.py     — seção Meu Perfil (~70 linhas)
    __init__.py    — sidebar + roteamento (~70 linhas)
"""

import streamlit as st

from modules.auth import obter_criancas_do_usuario
from utils.css_loader import inject_css

from ._constants import LABEL_PERFIL, NAV
from ._hoje import render_hoje
from ._historico import render_historico
from ._crianca import render_crianca
from ._vinculos import render_vinculos
from ._perfil import render_perfil


def render() -> None:
    inject_css('picta_design.css')

    usuario    = st.session_state.get('usuario', {})
    nome       = usuario.get('nome', '')
    usuario_id = usuario.get('id')
    perfil     = usuario.get('perfil', '')
    primeiro   = nome.split()[0] if nome else ''
    label      = LABEL_PERFIL.get(perfil, 'Usuário')
    criancas   = obter_criancas_do_usuario(usuario_id, perfil)

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

        # Seletor de criança
        crianca_id, crianca_nome = None, ''
        if criancas:
            st.markdown('<div class="sidebar-select-label">Acompanhando</div>',
                        unsafe_allow_html=True)
            nomes = [c['nome'] for c in criancas]
            sel   = st.selectbox("Criança", nomes, key="cui_sel",
                                 label_visibility="collapsed")
            crianca_id   = next(c['id'] for c in criancas if c['nome'] == sel)
            crianca_nome = sel

        st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)

        if 'cui_pag' not in st.session_state:
            st.session_state['cui_pag'] = 'hoje'

        for chave, emoji, titulo, desc in NAV:
            ativo = (st.session_state['cui_pag'] == chave)
            if st.button(f"{emoji}  {titulo}", key=f"cui_nav_{chave}",
                         use_container_width=True,
                         type="primary" if ativo else "secondary"):
                st.session_state['cui_pag'] = chave
                st.rerun()
            if ativo:
                st.markdown(f'<div class="nav-desc">{desc}</div>',
                            unsafe_allow_html=True)

        st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)

        st.markdown(
            f'<div class="sidebar-profile">'
            f'  <div class="sidebar-profile-top">'
            f'    <div class="sidebar-avatar-lg">👨‍👩‍👧</div>'
            f'    <div style="overflow:hidden">'
            f'      <div class="sidebar-profile-name">{nome}</div>'
            f'      <div class="sidebar-profile-role">{label}</div>'
            f'    </div></div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Encerrar Sessão", key="cui_logout", use_container_width=True):
            from controllers.auth_controller import logout
            logout()

    # Roteamento
    pag = st.session_state.get('cui_pag', 'hoje')
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
