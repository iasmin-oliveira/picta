"""
PICTA — views/dashboard_profissional/__init__.py
Ponto de entrada do dashboard Clínico / Profissional de Saúde.

Estrutura do pacote:
    _constants.py   — constantes compartilhadas
    _painel.py      — Painel Clínico: KPIs, alertas, diário (~120 linhas)
    _pacientes.py   — Pacientes: lista e cards (~80 linhas)
    _insights.py    — Insights IA: gráficos + relatório (~200 linhas)
    _exportacao.py  — Exportação: CSV + PDF (~90 linhas)
    _perfil.py      — Meu Perfil: edição de conta (~70 linhas)
    __init__.py     — sidebar + roteamento (~80 linhas)
"""

import streamlit as st

from modules.auth import obter_criancas_do_usuario
from utils.css_loader import inject_css

from ._constants import NAV
from ._painel import render_painel
from ._pacientes import render_pacientes
from ._insights import render_insights
from ._exportacao import render_exportacao
from ._perfil import render_perfil


def render() -> None:
    inject_css('picta_design.css')

    usuario    = st.session_state.get('usuario', {})
    nome       = usuario.get('nome', '')
    usuario_id = usuario.get('id')
    primeiro   = nome.split()[0] if nome else ''
    iniciais   = ''.join(p[0].upper() for p in nome.split()[:2]) or 'P'
    criancas   = obter_criancas_do_usuario(usuario_id, 'profissional')

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            '<p style="font-size:.65rem;font-weight:800;text-transform:uppercase;'
            'letter-spacing:.1em;color:#9ca3af;margin:0 0 .6rem .2rem">'
            'PROFISSIONAL DE SAÚDE</p>'
            '<div class="sidebar-logo">'
            '  <div class="sidebar-logo-icon">'
            '    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22"'
            '      viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"'
            '      stroke-linecap="round" stroke-linejoin="round">'
            '      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'
            '    </svg>'
            '  </div>'
            '  <span class="sidebar-logo-text">PICTA</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        crianca_id, crianca_nome = None, ''
        if criancas:
            st.markdown(
                '<p style="font-size:.68rem;font-weight:800;text-transform:uppercase;'
                'letter-spacing:.08em;color:#9ca3af;margin:.8rem 0 .3rem .2rem">'
                'PACIENTE</p>',
                unsafe_allow_html=True,
            )
            nomes = [c['nome'] for c in criancas]
            sel   = st.selectbox("Paciente", nomes, key="prof_sel",
                                 label_visibility="collapsed")
            crianca_id   = next(c['id'] for c in criancas if c['nome'] == sel)
            crianca_nome = sel

        st.markdown(
            '<hr style="border:none;border-top:1px solid #e5e7eb;margin:.7rem 0"/>',
            unsafe_allow_html=True,
        )

        if 'prof_pag' not in st.session_state:
            st.session_state['prof_pag'] = 'painel'

        for chave, emoji, titulo, desc in NAV:
            ativo = st.session_state['prof_pag'] == chave
            if st.button(
                f"{emoji}  {titulo}",
                key=f"prof_nav_{chave}",
                use_container_width=True,
                type="primary" if ativo else "secondary",
            ):
                st.session_state['prof_pag'] = chave
                st.rerun()
            if ativo:
                st.markdown(
                    f'<p style="font-size:.72rem;color:#6b7280;font-weight:600;'
                    f'padding:0 0 .4rem 1rem;margin:0">{desc}</p>',
                    unsafe_allow_html=True,
                )

        st.markdown(
            '<hr style="border:none;border-top:1px solid #e5e7eb;margin:.7rem 0"/>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div style="display:flex;align-items:center;gap:.6rem;padding:.4rem 0">'
            f'  <div style="width:32px;height:32px;border-radius:50%;'
            f'  background:#e0e7ff;display:flex;align-items:center;justify-content:center;'
            f'  font-size:.8rem;font-weight:800;color:#4338ca;flex-shrink:0">{iniciais}</div>'
            f'  <div style="overflow:hidden;min-width:0">'
            f'    <div style="font-size:.82rem;font-weight:800;color:#1e1b4b;'
            f'    white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{nome}</div>'
            f'    <div style="font-size:.7rem;color:#9ca3af;font-weight:600">'
            f'    Profissional de Saúde</div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("Encerrar Sessão", key="prof_logout", use_container_width=True):
            from controllers.auth_controller import logout
            logout()

    # ── Roteamento ────────────────────────────────────────────────────────────
    pag = st.session_state.get('prof_pag', 'painel')

    if pag == 'perfil':
        render_perfil(usuario_id, nome, iniciais)
        return

    if pag == 'pacientes':
        render_pacientes(criancas)
        return

    if not criancas:
        st.markdown(
            '<div style="text-align:center;padding:4rem 2rem">'
            '  <div style="font-size:3.5rem;margin-bottom:1rem">🩺</div>'
            '  <div style="font-size:1.1rem;font-weight:800;color:#1e1b4b;margin-bottom:.5rem">'
            '    Nenhum paciente vinculado</div>'
            '  <div style="color:#9ca3af;font-weight:600">'
            '    Peça ao responsável da criança para te convidar pelo PICTA.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    if pag == 'painel':
        render_painel(crianca_id, crianca_nome, primeiro)
    elif pag == 'insights':
        render_insights(crianca_id, crianca_nome)
    elif pag == 'exportar':
        render_exportacao(crianca_id, crianca_nome)
