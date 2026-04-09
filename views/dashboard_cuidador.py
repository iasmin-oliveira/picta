"""
PICTA — views/dashboard_cuidador.py
Dashboard analítico do Cuidador/Terapeuta. Ciclo 1 — estrutura base.
"""

import datetime
import streamlit as st
from modules.auth import obter_criancas_do_cuidador
from modules.logs import obter_interacoes
from utils.css_loader import inject_css

CORES = {
    'emocao':      {'bg': '#FFE8D8', 'text': '#8B3A00'},
    'acao':        {'bg': '#D6E8FF', 'text': '#1A3F7A'},
    'necessidade': {'bg': '#D4F0E4', 'text': '#155F40'},
}


def render():
    inject_css('dashboard_cuidador.css')

    usuario     = st.session_state.get('usuario', {})
    nome        = usuario.get('nome', 'Cuidador')
    cuidador_id = usuario.get('id')

    col_hdr, col_sair = st.columns([6, 1])
    with col_hdr:
        st.markdown(
            '<div class="dash-header">'
            '<div><h2>📊 Dashboard — Olá, ' + nome.split()[0] + '!</h2>'
                '<p>👩‍⚕️ Perfil Cuidador / Terapeuta - Área Restrita</p></div>'
            '<div style="font-size:2rem">🌿</div>'
            '</div>',
            unsafe_allow_html=True
        )
    with col_sair:
        if st.button("🚪 Sair", key="btn_sair_dash"):
            from controllers.auth_controller import logout
            logout()

    criancas = obter_criancas_do_cuidador(cuidador_id)
    if not criancas:
        st.info("Nenhuma criança vinculada a este perfil ainda.")
        return

    crianca_sel = st.selectbox("Selecionar criança:", [c['nome'] for c in criancas])
    crianca_id  = next(c['id'] for c in criancas if c['nome'] == crianca_sel)

    interacoes = obter_interacoes(crianca_id)
    hoje = datetime.date.today().isoformat()
    total          = len(interacoes)
    cliques_hoje   = sum(1 for i in interacoes if i.get('registado_em', '')[:10] == hoje)
    emocoes_hoje   = sum(1 for i in interacoes if i.get('categoria') == 'emocao' and i.get('registado_em', '')[:10] == hoje)

    c1, c2, c3 = st.columns(3)
    c1.metric("🖱️ Interações totais", total)
    c2.metric("📅 Cliques hoje", cliques_hoje)
    c3.metric("😊 Emoções hoje", emocoes_hoje)

    st.divider()
    st.markdown("#### 📋 Últimas interaçõe registadas")

    if interacoes:
        for reg in interacoes[:10]:
            cat = reg.get('categoria', '')
            cor = CORES.get(cat, {'bg': '#F3F4F6', 'text': '#6B7280'})
            ts  = str(reg.get('registado_em', ''))[:16]
            emoji = reg.get('emoji', '')
            nome_pic = reg.get('pictograma', '')
            bg   = cor['bg']
            txt  = cor['text']
            badge = (
                "<span style='background:" + bg + ";padding:2px 8px;"
                "border-radius:8px;font-size:0.78rem;color:" + txt + ";"
                "font-weight:700'>" + cat.upper() + "</span>"
            )
            st.markdown(
                "`" + ts + "` -> " + emoji + " **" + nome_pic + "** " + badge,
                unsafe_allow_html=True
            )
    else:
        st.info("Nenhuma interacao registada ainda.")

    st.divider()
    st.markdown(
        '<div class="coming-soon">'
        '<div style="font-size:2.5rem">🚧</div>'
        '<h4 style="margin:0.5rem 0">Graficos analiticos - Ciclo 3</h4>'
        '<p style="color:#8B7EA8;font-size:0.9rem;margin:0">'
        'Graficos Pandas e exportacao CSV/PDF no Ciclo 3 (16/05 a 22/06).'
        '</p></div>',
        unsafe_allow_html=True
    )
