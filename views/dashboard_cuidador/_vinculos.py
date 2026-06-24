"""
PICTA — views/dashboard_cuidador/_vinculos.py
Seção "Vínculos" do dashboard do cuidador.
"""

import streamlit as st

from modules.auth import (
    obter_criancas_do_usuario,
    vincular_crianca_responsavel,
    convidar_profissional,
    listar_profissionais_da_crianca,
)
from ._constants import _GRADS


def render_vinculos(usuario_id, perfil: str, criancas) -> None:
    st.markdown(
        '<div class="page-header">'
        '  <div class="page-title">🔗 Vínculos</div>'
        '  <div class="page-subtitle">'
        '    Adicione crianças ao seu painel e convide profissionais de saúde.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    criancas_resp = obter_criancas_do_usuario(usuario_id, perfil)
    col_add, col_list = st.columns([1, 1])

    with col_add:
        st.markdown('<div class="sec-header">🧒 Vincular criança</div>',
                    unsafe_allow_html=True)
        st.caption(
            "Informe o **nome de usuário** da criança (definido no cadastro) "
            "para vinculá-la ao seu painel."
        )
        with st.form("form_crianca"):
            uname = st.text_input("Nome de usuário da criança", placeholder="Ex: joao2018")
            if st.form_submit_button("➕ Vincular", use_container_width=True, type="primary"):
                if not uname.strip():
                    st.error("Informe o nome de usuário.")
                else:
                    erro = vincular_crianca_responsavel(usuario_id, uname)
                    if erro:
                        st.error(f"❌ {erro}")
                    else:
                        st.success("✅ Criança vinculada!")
                        st.rerun()

        if criancas_resp:
            st.markdown('<div class="sec-header">👩‍⚕️ Convidar profissional</div>',
                        unsafe_allow_html=True)
            st.caption(
                "Convide um médico, terapeuta ou fonoaudiólogo para acompanhar "
                "as comunicações da criança pelo PICTA."
            )
            with st.form("form_prof"):
                uname_p   = st.text_input("Nome de usuário do profissional",
                                          placeholder="Ex: dra.ana")
                crianca_p = st.selectbox("Para qual criança?",
                                         [c['nome'] for c in criancas_resp])
                cid_p = next(c['id'] for c in criancas_resp if c['nome'] == crianca_p)
                if st.form_submit_button("📨 Convidar", use_container_width=True, type="primary"):
                    if not uname_p.strip():
                        st.error("Informe o nome de usuário.")
                    else:
                        erro = convidar_profissional(usuario_id, uname_p, cid_p)
                        if erro:
                            st.error(f"❌ {erro}")
                        else:
                            st.success("✅ Profissional convidado!")
                            st.rerun()

    with col_list:
        if not criancas_resp:
            st.markdown(
                '<div class="glass-card" style="text-align:center;padding:2rem;">'
                '  <div style="font-size:2.5rem;margin-bottom:.75rem">🧩</div>'
                '  <div style="font-weight:800;color:#1e1b4b">Nenhuma criança vinculada</div>'
                '  <div style="color:#9ca3af;font-size:.88rem;font-weight:600;margin-top:.4rem">'
                '    Use o formulário ao lado.</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            return

        st.markdown(
            f'<div class="sec-header">👶 Crianças vinculadas ({len(criancas_resp)})</div>',
            unsafe_allow_html=True,
        )
        for idx, c in enumerate(criancas_resp):
            profs = listar_profissionais_da_crianca(c['id'])
            grad  = _GRADS[idx % len(_GRADS)]
            profs_html = ''.join(
                f'<div style="font-size:.8rem;color:#4b5563;font-weight:600;'
                f'padding:.3rem 0;border-top:1px dashed #e0e7ff;">'
                f'  👩‍⚕️ {p["nome"]}'
                f'  <span style="color:#9ca3af;font-size:.72rem"> · @{p["username"]}</span>'
                f'</div>'
                for p in profs
            ) if profs else (
                '<div style="font-size:.8rem;color:#9ca3af;font-style:italic;">'
                'Nenhum profissional vinculado ainda</div>'
            )
            st.markdown(
                f'<div class="patient-card">'
                f'  <div class="patient-card-top" style="background:{grad}">'
                f'    <span class="status-badge status-green">ATIVO</span>'
                f'  </div>'
                f'  <div class="patient-card-body">'
                f'    <div class="patient-card-avatar">🧒</div>'
                f'    <div class="patient-card-name">{c["nome"]}</div>'
                f'    <div class="patient-card-sub" style="color:#6366f1">'
                f'      {len(profs)} profissional(is) vinculado(s)</div>'
                f'    {profs_html}'
                f'  </div>'
                f'</div>',
                unsafe_allow_html=True,
            )
