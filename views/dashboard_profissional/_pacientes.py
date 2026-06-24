"""
PICTA — views/dashboard_profissional/_pacientes.py
Seção "Pacientes" do dashboard profissional.
"""

import datetime
import streamlit as st

from modules.logs import APP_TZ, obter_interacoes
from ._constants import _GRADS


def render_pacientes(criancas) -> None:
    st.markdown(
        '<div class="page-header">'
        '  <div class="page-title">👥 Pacientes</div>'
        '  <div class="page-subtitle">'
        '    Visão geral de todos os pacientes vinculados ao seu atendimento.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    if not criancas:
        st.markdown(
            '<div style="text-align:center;padding:3rem">'
            '  <div style="font-size:3.5rem;margin-bottom:1rem">🩺</div>'
            '  <div style="font-size:1.1rem;font-weight:800;color:#1e1b4b;margin-bottom:.5rem">'
            '    Nenhum paciente vinculado</div>'
            '  <div style="color:#9ca3af;font-weight:600">'
            '    Peça ao responsável para te convidar pelo PICTA.</div>'
            '</div>'
            '<div style="border:3px dashed #e0e7ff;border-radius:28px;padding:2.5rem;'
            'text-align:center;color:#9ca3af;margin-top:.5rem">'
            '  <div style="font-size:2rem;margin-bottom:.5rem">＋</div>'
            '  <div style="font-weight:800;font-size:.95rem">Aguardando vínculo</div>'
            '  <div style="font-size:.82rem;margin-top:.3rem">'
            '    O responsável deve informar seu @username ao convidar</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    hoje = datetime.datetime.now(APP_TZ).date()
    for i in range(0, len(criancas), 3):
        grupo = criancas[i:i + 3]
        cols  = st.columns(len(grupo))
        for col, c in zip(cols, grupo):
            interacs    = obter_interacoes(c['id'], limite=1)
            ultima_data = (
                str(interacs[0].get('registado_em', ''))[:10] if interacs else None
            )
            try:
                ativo = bool(
                    ultima_data and
                    (hoje - datetime.date.fromisoformat(ultima_data)).days <= 7
                )
            except Exception:
                ativo = False

            grad       = _GRADS[criancas.index(c) % len(_GRADS)]
            initials   = ''.join(p[0].upper() for p in c['nome'].split()[:2])
            status_cls = "status-green" if ativo else "status-orange"
            status_lbl = "ATIVO" if ativo else "INATIVO"
            sub_txt    = "Ativo nos últimos 7 dias" if ativo else "Sem atividade recente"

            with col:
                st.markdown(
                    f'<div class="patient-card">'
                    f'  <div class="patient-card-top" style="background:{grad}">'
                    f'    <span class="status-badge {status_cls}">{status_lbl}</span>'
                    f'  </div>'
                    f'  <div class="patient-card-body">'
                    f'    <div class="patient-card-avatar">'
                    f'      <span style="font-size:1.4rem;font-weight:800;'
                    f'      background:linear-gradient(135deg,#4f46e5,#8b5cf6);'
                    f'      -webkit-background-clip:text;-webkit-text-fill-color:transparent">'
                    f'      {initials}</span>'
                    f'    </div>'
                    f'    <div class="patient-card-name">{c["nome"]}</div>'
                    f'    <div class="patient-card-sub" style="color:#6366f1">{sub_txt}</div>'
                    f'  </div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Ver Painel", key=f"ver_{c['id']}", use_container_width=True):
                    st.session_state['prof_pag'] = 'painel'
                    st.rerun()

    st.markdown(
        '<div style="border:3px dashed #e0e7ff;border-radius:28px;'
        'padding:2rem;text-align:center;color:#9ca3af;margin-top:.5rem">'
        '  <div style="font-size:1.8rem;margin-bottom:.4rem">＋</div>'
        '  <div style="font-weight:800;font-size:.9rem">Vincular novo paciente</div>'
        '  <div style="font-size:.8rem;margin-top:.25rem">'
        '    Peça ao responsável para informar seu @username</div>'
        '</div>',
        unsafe_allow_html=True,
    )
