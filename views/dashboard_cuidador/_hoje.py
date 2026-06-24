"""
PICTA — views/dashboard_cuidador/_hoje.py
Seção "Hoje" do dashboard do cuidador.
"""

import datetime
import streamlit as st
from collections import Counter

from modules.logs import APP_TZ, obter_interacoes
from ._constants import FRASE_EMOCAO, EMOCOES_ATENCAO


def render_hoje(criancas, crianca_id, crianca_nome, primeiro_nome: str) -> None:
    nome_curto = crianca_nome.split()[0] if crianca_nome else ''
    st.markdown(
        f'<div class="page-header">'
        f'  <div class="page-title">Olá, {primeiro_nome}! 👋</div>'
        f'  <div class="page-subtitle">Aqui está o que <b>{nome_curto or "sua criança"}</b>'
        f'  comunicou hoje pelo PICTA.</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if not criancas or not crianca_id:
        st.markdown(
            '<div class="glass-card" style="text-align:center;padding:3rem;">'
            '  <div style="font-size:3.5rem;margin-bottom:1rem">🧩</div>'
            '  <div style="font-size:1.1rem;font-weight:800;color:#1e1b4b;margin-bottom:.5rem">'
            '    Nenhuma criança vinculada ainda</div>'
            '  <div style="color:#9ca3af;font-weight:600">'
            '    Acesse <b>Vínculos</b> no menu para adicionar.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    col_r, col_i = st.columns([1, 4])
    with col_r:
        if st.button("🔄 Atualizar", key="cui_refresh"):
            st.rerun()
    with col_i:
        st.caption(f"Última atualização: {datetime.datetime.now(APP_TZ).strftime('%H:%M')}")

    interacoes = obter_interacoes(crianca_id)
    hoje_str  = datetime.datetime.now(APP_TZ).date().isoformat()
    hoje_ints = [i for i in interacoes if str(i.get('registado_em', ''))[:10] == hoje_str]
    emocoes    = [i for i in hoje_ints if i.get('categoria') == 'emocao']
    acoes      = [i for i in hoje_ints if i.get('categoria') == 'acao']
    necs       = [i for i in hoje_ints if i.get('categoria') == 'necessidade']

    if not hoje_ints:
        st.markdown(
            f'<div class="glass-card" style="text-align:center;padding:3rem;">'
            f'  <div style="font-size:3.5rem;margin-bottom:1rem">☀️</div>'
            f'  <div style="font-size:1.05rem;font-weight:800;color:#1e1b4b;margin-bottom:.5rem">'
            f'    {nome_curto} ainda não usou o PICTA hoje</div>'
            f'  <div style="color:#9ca3af;font-weight:600">'
            f'    Quando {nome_curto} se comunicar, tudo aparece aqui.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        _banner_total(interacoes, nome_curto)
        return

    # Hero emocional
    em_top = Counter(i['pictograma'] for i in emocoes).most_common(1)
    if em_top:
        em_nome  = em_top[0][0]
        em_vezes = em_top[0][1]
        em_emoji = next((i['emoji'] for i in emocoes if i['pictograma'] == em_nome), '😶')
        frase    = FRASE_EMOCAO.get(em_nome, f'demonstrou {em_nome.lower()}')
        st.markdown(
            f'<div class="wb-hero">'
            f'  <span class="wb-emoji">{em_emoji}</span>'
            f'  <div class="wb-phrase">Hoje {nome_curto} {frase}</div>'
            f'  <div class="wb-sub">{em_vezes}× — emoção mais expressada</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Mini stats
    c1, c2, c3 = st.columns(3)
    _mini_stat(c1, str(len(hoje_ints)), "comunicações hoje",    "🖐️")
    _mini_stat(c2, str(len(emocoes)),   "sentimentos expressos", "❤️")
    _mini_stat(c3, str(len(necs)),      "pedidos feitos",        "🙋")

    # Pedidos e Ações
    if necs or acoes:
        col_n, col_a = st.columns(2)
        with col_n:
            if necs:
                st.markdown('<div class="sec-header">🙋 O que pediu hoje</div>',
                            unsafe_allow_html=True)
                for pict, qtd in Counter(i['pictograma'] for i in necs).most_common():
                    em = next((i['emoji'] for i in necs if i['pictograma'] == pict), '')
                    _diary_item(em, pict.title(), f"{qtd}× solicitado",
                                'badge-necessidade', 'Pedido')
        with col_a:
            if acoes:
                st.markdown('<div class="sec-header">🎯 O que fez hoje</div>',
                            unsafe_allow_html=True)
                for pict, qtd in Counter(i['pictograma'] for i in acoes).most_common():
                    em = next((i['emoji'] for i in acoes if i['pictograma'] == pict), '')
                    _diary_item(em, pict.title(), f"{qtd}× realizado",
                                'badge-acao', 'Ação')

    # Dicas do dia
    dicas = []
    if necs:
        top = Counter(i['pictograma'] for i in necs).most_common(1)[0][0].lower()
        dicas.append(f"{nome_curto} pediu <b>{top}</b> hoje. Que tal oferecer à tarde?")
    if [i for i in emocoes if i['pictograma'] in EMOCOES_ATENCAO]:
        dicas.append(f"{nome_curto} demonstrou emoções de atenção hoje. Uma atividade calma pode ajudar.")
    if acoes:
        top_a = Counter(i['pictograma'] for i in acoes).most_common(1)[0][0].lower()
        dicas.append(f"{nome_curto} quis <b>{top_a}</b> hoje — ótimo sinal de engajamento!")
    if dicas:
        st.markdown('<div style="margin-top:.25rem"></div>', unsafe_allow_html=True)
        for d in dicas:
            st.markdown(f'<div class="tip-card">💡 {d}</div>', unsafe_allow_html=True)

    _banner_total(interacoes, nome_curto)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _banner_total(interacoes: list, nome_curto: str) -> None:
    if interacoes:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#4f46e5,#8b5cf6);'
            f'border-radius:16px;padding:1rem 1.4rem;text-align:center;'
            f'color:rgba(255,255,255,.85);font-size:.88rem;font-weight:700;'
            f'box-shadow:0 4px 15px rgba(79,70,229,.25);margin-top:.5rem;">'
            f'No total, {nome_curto} fez '
            f'<b style="color:#fff;font-size:1rem">{len(interacoes)}</b>'
            f' comunicações pelo PICTA.</div>',
            unsafe_allow_html=True,
        )


def _mini_stat(col, valor: str, desc: str, icon: str) -> None:
    with col:
        st.markdown(
            f'<div class="mini-stat">'
            f'  <div class="mini-stat-icon">{icon}</div>'
            f'  <div class="mini-stat-value">{valor}</div>'
            f'  <div class="mini-stat-label">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _diary_item(emoji: str, nome: str, tempo: str,
                badge_cls: str, badge_txt: str) -> None:
    st.markdown(
        f'<div class="diary-item">'
        f'  <div class="diary-emoji">{emoji}</div>'
        f'  <div><div class="diary-name">{nome}</div>'
        f'  <div class="diary-time">{tempo}</div></div>'
        f'  <span class="diary-badge {badge_cls}">{badge_txt}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
