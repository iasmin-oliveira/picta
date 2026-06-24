"""
PICTA — views/dashboard_profissional/_perfil.py
Seção "Meu Perfil" do dashboard profissional.
"""

import streamlit as st

from modules.auth import obter_usuario_por_id, atualizar_usuario


def render_perfil(usuario_id, nome: str, iniciais: str) -> None:
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

    col_card, col_form = st.columns([1, 1])

    with col_card:
        st.markdown(
            f'<div class="glass-card" style="text-align:center;padding:2rem">'
            f'  <div style="display:flex;justify-content:center;margin-bottom:1.2rem">'
            f'    <div class="profile-avatar-xl">{iniciais}</div>'
            f'  </div>'
            f'  <div class="profile-name-big">{nome_atual}</div>'
            f'  <div style="margin-top:.4rem">'
            f'    <span class="profile-role-badge">👩‍⚕️ Profissional de Saúde</span>'
            f'  </div>'
            f'  <div class="ficha-row" style="margin-top:1.2rem">'
            f'    <span class="ficha-label">Nome de usuário</span>'
            f'    <span class="ficha-valor">@{username_atual}</span>'
            f'  </div>'
            f'  <div class="ficha-row">'
            f'    <span class="ficha-label">Tipo de conta</span>'
            f'    <span class="ficha-valor">Profissional</span>'
            f'  </div>'
            f'</div>'
            f'<div class="glass-card" style="padding:1rem 1.2rem;margin-top:.8rem">'
            f'  <div class="sec-header" style="margin-bottom:.5rem">🔒 Segurança</div>'
            f'  <div style="font-size:.82rem;color:#4b5563;font-weight:600;line-height:1.6">'
            f'    Senha armazenada de forma criptografada. '
            f'    Nunca compartilhe com colegas ou pacientes. '
            f'    Use pelo menos 6 caracteres.'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_form:
        st.markdown(
            '<div class="sec-header">✏️ Editar informações</div>',
            unsafe_allow_html=True,
        )
        with st.form("form_perfil_prof"):
            novo_nome     = st.text_input("Nome completo", value=nome_atual)
            novo_username = st.text_input(
                "Nome de usuário", value=username_atual,
                help="Letras, números e ponto. Ex: dra.marina",
            )
            st.caption("🔑 Alterar senha — deixe em branco para manter a atual")
            nova_senha = st.text_input("Nova senha", type="password",
                                       placeholder="Mínimo 6 caracteres")
            conf_senha = st.text_input("Confirmar nova senha", type="password")

            if st.form_submit_button("💾 Salvar alterações",
                                     use_container_width=True, type="primary"):
                if nova_senha and nova_senha != conf_senha:
                    st.error("❌ As senhas não coincidem.")
                else:
                    erro = atualizar_usuario(
                        usuario_id, novo_nome, novo_username,
                        nova_senha if nova_senha else "",
                    )
                    if erro:
                        st.error(f"❌ {erro}")
                    else:
                        st.session_state['usuario']['nome'] = novo_nome
                        st.success("✅ Perfil atualizado com sucesso!")
                        st.rerun()
