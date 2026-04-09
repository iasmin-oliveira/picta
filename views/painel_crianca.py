"""
PICTA — views/painel_crianca.py
Interface principal da criança: grade de pictogramas (Método DHACA).
RF02 · RF03 · RNF01
"""

import streamlit as st
from database.db import executar
from modules.logs import registar_interacao
from modules.auth import obter_crianca_por_usuario_id
from utils.css_loader import inject_css


def render():
    inject_css('painel_crianca.css')

    usuario  = st.session_state.get('usuario', {})
    nome     = usuario.get('nome', 'Criança')
    user_id  = usuario.get('id')

    crianca_info = obter_crianca_por_usuario_id(user_id)
    crianca_id   = crianca_info['id'] if crianca_info else 1

    # ── Cabeçalho ─────────────────────────────────────
    col_hdr, col_sair = st.columns([5, 1])
    with col_hdr:
        st.markdown(f"""
        <div class="header-crianca">
            <div class="header-textos">
                <div class="saudacao">👋 Olá, {nome.split()[0]}!</div>
                <div class="subtitulo">Como você está se sentindo agora?</div>
            </div>
            <div style="font-size:2rem">🌈</div>
        </div>
        """, unsafe_allow_html=True)

    with col_sair:
        st.markdown('<div id="logout-container">', unsafe_allow_html=True)
        if st.button("🚪 Sair", key="logout_btn"):
            from controllers.auth_controller import logout
            logout()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Feedback ──────────────────────────────────────
    if 'feedback' in st.session_state:
        msg = st.session_state.pop('feedback')
        st.success(msg) if msg.startswith('✅') else st.error(msg)

    # ── Grade de pictogramas ──────────────────────────
    pictogramas = _obter_pictogramas()
    config = {
        'emocao':      ('😊 Como me sinto',    'cat-emocao',      'anchor-emocao'),
        'acao':        ('🎮 O que quero fazer', 'cat-acao',        'anchor-acao'),
        'necessidade': ('💧 O que preciso',     'cat-necessidade', 'anchor-necessidade'),
    }

    for cat_key, (cat_label, cat_class, anchor_class) in config.items():
        pics = pictogramas.get(cat_key, [])
        if not pics:
            continue

        st.markdown(
            f'<div class="categoria-titulo {cat_class}">{cat_label}</div>',
            unsafe_allow_html=True
        )

        cols = st.columns(4)
        for i, pic in enumerate(pics):
            with cols[i % 4]:
                st.markdown(f'<span class="{anchor_class}"></span>', unsafe_allow_html=True)
                if st.button(
                    f"{pic['emoji']}\n\n**{pic['nome']}**",
                    key=f"pic_{pic['id']}",
                    use_container_width=True
                ):
                    ok = registar_interacao(crianca_id, pic['id'])
                    st.session_state['feedback'] = (
                        f"✅  {pic['emoji']} **{pic['nome']}** registado!"
                        if ok else "⚠️  Algo correu mal. Tente novamente."
                    )
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)


def _obter_pictogramas() -> dict:
    rows = executar(
        "SELECT id, nome, categoria, emoji FROM Pictogramas ORDER BY categoria, nome",
        fetchall=True
    ) or []
    grupos = {'emocao': [], 'acao': [], 'necessidade': []}
    for r in rows:
        if r['categoria'] in grupos:
            grupos[r['categoria']].append(r)
    return grupos
