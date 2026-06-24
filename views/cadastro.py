"""
PICTA — views/cadastro.py

Tela de cadastro com vínculo imediato:
- Criança: pode informar o username do responsável para ser vinculada
- Responsável: pode informar o username de uma criança para vinculá-la
- Profissional: cadastro simples (responsável faz o vínculo pelo dashboard)
"""

import streamlit as st
from database.db import executar
from modules.auth import criar_usuario, vincular_crianca_responsavel, criar_crianca_para_utilizador
from utils.css_loader import inject_css

PERFIS = {
    'crianca':      ('🧒 Criança',                  'A própria criança utilizará o painel'),
    'responsavel':  ('👨‍👩‍👧 Responsável',            'Pai, mãe ou tutor que acompanha a criança'),
    'profissional': ('👩‍⚕️ Profissional de Saúde',   'Terapeuta, fonoaudiólogo, psicopedagogo'),
}


def render() -> None:
    inject_css('login.css')

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""
        <div class="picta-logo">
            <div class="star">🌈</div>
            <h1>PICTA</h1>
            <p>Criar nova conta</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("form_cadastro", clear_on_submit=False):
            nome      = st.text_input("👤  Nome completo", placeholder="Ex: Maria Silva")
            username  = st.text_input("🔑  Nome de utilizador", placeholder="Ex: maria.silva (sem espaços)")
            senha     = st.text_input("🔒  Senha", type="password", placeholder="Mínimo 6 caracteres")
            confirmar = st.text_input("🔒  Confirmar senha", type="password", placeholder="Repita a senha")

            st.markdown("---")
            st.markdown("**Qual é o seu perfil?**")
            perfil = st.radio(
                "perfil",
                options=list(PERFIS.keys()),
                format_func=lambda k: PERFIS[k][0],
                label_visibility="collapsed",
            )
            st.caption(PERFIS[perfil][1])

            # Campo de vínculo contextual
            username_vinculo = ""
            if perfil == 'crianca':
                st.markdown("---")
                username_vinculo = st.text_input(
                    "👨‍👩‍👧  Username do responsável *(opcional)*",
                    placeholder="Ex: maria.silva",
                    help="Se informar, sua conta será vinculada ao responsável automaticamente.",
                )
            elif perfil == 'responsavel':
                st.markdown("---")
                username_vinculo = st.text_input(
                    "🧒  Username da criança *(opcional)*",
                    placeholder="Ex: joao",
                    help="Se a criança já tiver conta, informe o username para vinculá-la.",
                )

            submitted = st.form_submit_button("✨  Criar conta", use_container_width=True)

        if submitted:
            if senha != confirmar:
                st.error("❌  As senhas não coincidem.")
            else:
                erro = criar_usuario(nome, username, senha, perfil)
                if erro:
                    st.error("❌  " + erro)
                else:
                    # Criar registo em Criancas se for criança
                    if perfil == 'crianca':
                        user_row = executar(
                            "SELECT id FROM Utilizadores WHERE username = ?",
                            (username.strip().lower(),),
                            fetchone=True,
                        )
                        if user_row:
                            criar_crianca_para_utilizador(user_row['id'], nome.strip())

                    # Processar vínculo opcional
                    msg_vinculo = ""
                    if username_vinculo.strip():
                        user_row = executar(
                            "SELECT id FROM Utilizadores WHERE username = ?",
                            (username.strip().lower(),),
                            fetchone=True,
                        )
                        if user_row:
                            if perfil == 'crianca':
                                # Vincular esta criança ao responsável informado
                                resp = executar(
                                    "SELECT id FROM Utilizadores WHERE username = ? AND perfil = 'responsavel'",
                                    (username_vinculo.strip().lower(),),
                                    fetchone=True,
                                )
                                if resp:
                                    crianca_row = executar(
                                        "SELECT id FROM Criancas WHERE utilizador_id = ?",
                                        (user_row['id'],),
                                        fetchone=True,
                                    )
                                    if crianca_row:
                                        executar(
                                            "UPDATE Criancas SET cuidador_id = ? WHERE id = ?",
                                            (resp['id'], crianca_row['id']),
                                            commit=True,
                                        )
                                        msg_vinculo = " Vinculada ao responsável com sucesso."
                                    else:
                                        msg_vinculo = " (Responsável não encontrado ou sem permissão.)"
                                else:
                                    msg_vinculo = " (Responsável não encontrado.)"

                            elif perfil == 'responsavel':
                                erro_v = vincular_crianca_responsavel(user_row['id'], username_vinculo)
                                if erro_v:
                                    msg_vinculo = " (" + erro_v + ")"
                                else:
                                    msg_vinculo = " Criança vinculada com sucesso."

                    st.success("✅  Conta criada!" + msg_vinculo + " Faça login para entrar.")
                    st.session_state['tela'] = 'login'
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Voltar para o login", use_container_width=True, key="btn_voltar"):
            st.session_state['tela'] = 'login'
            st.rerun()

        st.markdown("""
        <p style="text-align:center;color:#8B7EA8;font-size:0.75rem;margin-top:1rem;">
            PICTA © 2026 · FACCAT · Sistemas de Informação
        </p>
        """, unsafe_allow_html=True)
