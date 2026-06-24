"""
PICTA — views/login.py
Tela de login com link para cadastro.
"""

import streamlit as st
from utils.css_loader import inject_css

# ────────────────────────────────────────────────────
#  CSS personalizado — identidade visual PICTA
# ────────────────────────────────────────────────────
def render_login_form():
    inject_css('login.css')

    # Centraliza o card com colunas
    _, col, _ = st.columns([1, 2, 1])

    with col:
        # ── Logo ──────────────────────────────────────────
        st.markdown("""
        <div class="picta-logo">
            <div class="star">🌈</div>
            <h1>PICTA</h1>
            <p>Assistente de Comunicação e Expressão Emocional</p>
        </div>
        """, unsafe_allow_html=True)

        # ── Badges de perfil ──────────────────────────────
        st.markdown("""
        <div class="badge-row">
            <span class="badge badge-crianca">🧒 Criança</span>
            <span class="badge badge-cuidador">👩‍⚕️ Responsável / Profissional</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        feedback = st.empty()

        # ── Formulário de login ───────────────────────────
        with st.form("form_login", clear_on_submit=False):
            username  = st.text_input("👶​🧒​👦 Login", placeholder="Digite seu usuário")
            senha     = st.text_input("🔒  Senha", type="password", placeholder="Digite sua senha")
            submitted = st.form_submit_button("✨  Entrar no PICTA", use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_txt, col_btn = st.columns([2, 1])
        with col_txt:
            st.markdown(
                "<p style='color:#8B7EA8;font-size:0.88rem;margin-top:0.6rem'>"
                "Ainda não tem conta?</p>",
                unsafe_allow_html=True
            )
        with col_btn:
            if st.button("Cadastrar-se", use_container_width=True, key="btn_cadastro"):
                st.session_state['tela'] = 'cadastro'
                st.rerun()

        st.markdown("""
        <p style="text-align:center;color:#8B7EA8;font-size:0.75rem;margin-top:1.5rem;">
            PICTA © 2026 · FACCAT · Sistemas de Informação
        </p>
        """, unsafe_allow_html=True)

    return username, senha, submitted, feedback
