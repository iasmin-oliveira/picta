"""
PICTA — views/dashboard_cuidador/_perfil.py
Seção "Meu Perfil" do dashboard do cuidador.
"""

import streamlit as st

from modules.auth import obter_usuario_por_id, atualizar_usuario


def render_perfil(usuario_id, nome: str, primeiro: str, label: str) -> None:
    st.markdown(
        '<div class="page-header">'
        '  <div class="page-title">👤 Meu Perfil</div>'
        '  <div class="page-subtitle">'
        '    Atualize seu nome de exibição, nome de usuário e senha.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    usuario_db     = obter_usuario_por_id(usuario_id)
    nome_atual     = usuario_db.get('nome', nome)   if usuario_db else nome
    username_atual = usuario_db.get('username', '') if usuario_db else ''
    iniciais       = ''.join(p[0].upper() for p in nome.split()[:2])

    col_card, col_form = st.columns([1, 1])

    with col_card:
        st.markdown(
            f'<div class="glass-card" style="text-align:center;padding:2rem;">'
            f'  <div style="display:flex;justify-content:center;margin-bottom:1.2rem">'
            f'    <div class="profile-avatar-xl">{iniciais}</div>'
            f'  </div>'
            f'  <div class="profile-name-big">{nome_atual}</div>'
            f'  <div style="margin-top:.4rem">'
            f'    <span class="profile-role-badge">👨‍👩‍👧 {label}</span>'
            f'  </div>'
            f'  <div class="ficha-row" style="margin-top:1.2rem">'
            f'    <span class="ficha-label">Nome de usuário</span>'
            f'    <span class="ficha-valor">@{username_atual}</span>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="glass-card" style="padding:1rem 1.2rem;">'
            '  <div class="sec-header" style="margin-bottom:.5rem">🔒 Segurança da conta</div>'
            '  <div style="font-size:.82rem;color:#4b5563;font-weight:600;line-height:1.6">'
            '    Sua senha é armazenada de forma criptografada. '
            '    Nunca a compartilhe. '
            '    Use pelo menos 6 caracteres combinando letras e números.'
            '  </div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with col_form:
        st.markdown('<div class="sec-header">✏️ Editar informações</div>',
                    unsafe_allow_html=True)
        with st.form("form_perfil_cuidador"):
            novo_nome     = st.text_input("Nome completo", value=nome_atual)
            novo_username = st.text_input("Nome de usuário", value=username_atual,
                                          help="Letras, números e ponto. Ex: maria.silva")
            st.markdown(
                '<div style="margin-top:.4rem;font-size:.78rem;color:#9ca3af;'
                'font-weight:600">🔑 Alterar senha — deixe em branco para manter a atual</div>',
                unsafe_allow_html=True,
            )
            nova_senha = st.text_input("Nova senha", type="password",
                                       placeholder="Mínimo 6 caracteres")
            conf_senha = st.text_input("Confirmar nova senha", type="password")

            if st.form_submit_button("💾 Salvar alterações", use_container_width=True,
                                     type="primary"):
                if nova_senha and nova_senha != conf_senha:
                    st.error("❌ As senhas não coincidem.")
                else:
                    erro = atualizar_usuario(usuario_id, novo_nome, novo_username,
                                             nova_senha if nova_senha else "")
                    if erro:
                        st.error(f"❌ {erro}")
                    else:
                        st.session_state['usuario']['nome'] = novo_nome
                        st.success("✅ Perfil atualizado com sucesso!")
                        st.rerun()
