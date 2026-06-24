"""
PICTA — views/dashboard_profissional/_painel.py
Seção "Painel Clínico" do dashboard profissional.
"""

import datetime
import streamlit as st
import pandas as pd
from collections import Counter

from modules.logs import APP_TZ, obter_interacoes
from utils.formatters import format_datetime_br
from ._constants import (
    EMOCOES_ALERTA, EMOCOES_POSITIVAS,
    COR_CAT, LABEL_CAT, BADGE_CAT,
)


def render_painel(crianca_id, crianca_nome: str, primeiro: str) -> None:
    nome_curto = crianca_nome.split()[0]

    st.markdown(
        f'<div class="page-header">'
        f'  <div class="page-title">Olá, Dr(a). {primeiro} 👋</div>'
        f'  <div class="page-subtitle">'
        f'    Acompanhamento clínico de <b>{crianca_nome}</b>'
        f'    — dados atualizados em tempo real.</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    interacoes = obter_interacoes(crianca_id, limite=500)
    if not interacoes:
        st.info("Nenhuma interação registrada para este paciente ainda.")
        return

    df = pd.DataFrame(interacoes)
    df['registado_em'] = pd.to_datetime(df['registado_em'])
    df['data'] = df['registado_em'].dt.date
    df['hora'] = df['registado_em'].dt.hour

    hoje    = datetime.datetime.now(APP_TZ).date()
    sem_df  = df[df['data'] >= hoje - datetime.timedelta(days=7)]
    em_df   = df[df['categoria'] == 'emocao']
    pct_neg = round(100 * len(em_df[em_df['pictograma'].isin(EMOCOES_ALERTA)])    / max(len(em_df), 1))
    pct_pos = round(100 * len(em_df[em_df['pictograma'].isin(EMOCOES_POSITIVAS)]) / max(len(em_df), 1))
    hora_pico = int(df.groupby('hora').size().idxmax())

    # KPI cards
    sub_sem = f"↑ {len(sem_df)} esta semana"
    st.markdown(
        '<div class="kpi-grid">'
        + _kpi_html("TOTAL",     str(len(df)),   sub_sem,        "kpi-sub-blue",   "kpi-accent-indigo")
        + _kpi_html("POSITIVAS", f"{pct_pos}%",  "emoções pos.", "kpi-sub-green",  "kpi-accent-green")
        + _kpi_html("ATENÇÃO",   f"{pct_neg}%",  "acompanhar",   "kpi-sub-orange", "kpi-accent-orange")
        + _kpi_html("PICO",      f"{hora_pico}h","mais ativo",   "kpi-sub-blue",   "kpi-accent-blue")
        + '</div>',
        unsafe_allow_html=True,
    )

    col_alert, col_dist = st.columns([1, 1])

    with col_alert:
        alertas = _calcular_alertas(df, nome_curto)
        alertas_html = ''.join(
            f'<div class="alert-card">{a}</div>' for a in alertas
        ) if alertas else (
            f'<div class="ok-card">'
            f'✅ Nenhum padrão crítico identificado para {nome_curto} no período recente.'
            f'</div>'
        )
        st.markdown(
            f'<div class="glass-card">'
            f'  <div class="sec-header">⚠️ Pontos de atenção</div>'
            f'  {alertas_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_dist:
        cat_count = df.groupby('categoria').size()
        total_cat = cat_count.sum()
        barras = ''
        for cat, cnt in cat_count.items():
            pct = int(100 * cnt / total_cat)
            cor = COR_CAT.get(cat, '#6366f1')
            lbl = LABEL_CAT.get(cat, cat.upper())
            barras += (
                f'<div style="display:flex;align-items:center;gap:.7rem;margin-bottom:.75rem">'
                f'  <span style="font-size:.72rem;font-weight:800;color:#374151;'
                f'  text-transform:uppercase;letter-spacing:.05em;min-width:4.5rem">{lbl}</span>'
                f'  <div style="flex:1;background:#f0f1f8;border-radius:50px;height:8px;overflow:hidden">'
                f'    <div style="width:{pct}%;height:100%;background:{cor};border-radius:50px"></div>'
                f'  </div>'
                f'  <span style="font-size:.8rem;font-weight:800;color:#6b7280;min-width:2.5rem;'
                f'  text-align:right">{pct}%</span>'
                f'</div>'
            )
        st.markdown(
            f'<div class="glass-card">'
            f'  <div class="sec-header">📊 Por categoria</div>'
            f'  {barras}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Diário visual
    itens = ''
    for _, reg in df.head(20).iterrows():
        cat   = reg.get('categoria', '')
        ts    = format_datetime_br(reg.get('registado_em'), sep=' · ')
        emoji = reg.get('emoji', '')
        pict  = reg.get('pictograma', '').title()
        badge_cls, badge_txt = BADGE_CAT.get(cat, ('badge-acao', cat.upper()))
        cor   = COR_CAT.get(cat, '#6366f1')
        itens += (
            f'<div class="diary-item" style="border-left:3px solid {cor}">'
            f'  <span style="font-size:.75rem;color:#6b7280;min-width:8.8rem;font-weight:800">'
            f'    {ts}</span>'
            f'  <span style="font-size:1.3rem;flex-shrink:0">{emoji}</span>'
            f'  <span style="font-size:.88rem;font-weight:800;color:#1e1b4b;flex:1">{pict}</span>'
            f'  <span class="diary-badge {badge_cls}">{badge_txt}</span>'
            f'</div>'
        )
    st.markdown(
        f'<div class="glass-card">'
        f'  <div class="sec-header">🕐 Diário visual — últimas interações</div>'
        f'  {itens}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Helpers ──────────────────────────────────────────────────────────────────

def _kpi_html(label: str, valor: str, sub: str, sub_cls: str, accent_cls: str) -> str:
    return (
        f'<div class="kpi-card {accent_cls}">'
        f'  <div class="kpi-label">{label}</div>'
        f'  <div class="kpi-value">{valor}</div>'
        f'  <div class="kpi-sub {sub_cls}">{sub}</div>'
        f'</div>'
    )


def _calcular_alertas(df, nome: str) -> list:
    alertas = []
    hoje = datetime.datetime.now(APP_TZ).date()
    sem  = df[df['data'] >= hoje - datetime.timedelta(days=7)]
    neg  = sem[sem['pictograma'].isin(EMOCOES_ALERTA)]
    if len(neg) >= 3:
        top = Counter(neg['pictograma']).most_common(1)[0]
        alertas.append(
            f"🌀 <b>{top[1]}×</b> a emoção <b>{top[0].lower()}</b> "
            f"nos últimos 7 dias — avaliar estado emocional."
        )
    noturno = int(((df['hora'] >= 23) | (df['hora'] <= 5)).sum())
    if noturno >= 3:
        alertas.append(
            f"🌙 <b>{noturno} interações noturnas</b> (23h–5h) "
            f"— investigar possível alteração do padrão de sono."
        )
    if not df.empty:
        dias_sem = (hoje - df['data'].max()).days
        if dias_sem >= 5:
            alertas.append(
                f"📵 <b>{dias_sem} dias sem interações</b> — verificar adesão ao aplicativo."
            )
    ajuda = int((df['pictograma'] == 'AJUDA').sum())
    if ajuda >= 3:
        alertas.append(
            f"🆘 <b>\"AJUDA\"</b> selecionada <b>{ajuda}×</b> "
            f"— verificar necessidade de suporte adicional."
        )
    return alertas
