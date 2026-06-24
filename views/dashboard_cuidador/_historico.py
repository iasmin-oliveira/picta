"""History section for the caregiver dashboard."""

from __future__ import annotations

import datetime

import pandas as pd
import streamlit as st

from modules.logs import APP_TZ, obter_interacoes
from utils.formatters import (
    filename_date,
    format_date_br,
    format_datetime_br,
    format_time,
    safe_filename,
)
from ._constants import BADGE_CAT, COR_CAT


def render_historico(criancas, crianca_id, crianca_nome: str) -> None:
    nome_curto = crianca_nome.split()[0] if crianca_nome else ""
    st.markdown(
        f'<div class="page-header">'
        f'  <div class="page-title">📅 Histórico</div>'
        f'  <div class="page-subtitle">'
        f'    Tudo que <b>{nome_curto}</b> comunicou, organizado por data.</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if not criancas or not crianca_id:
        st.info("Vincule uma criança para ver o histórico.")
        return

    interacoes = obter_interacoes(crianca_id, limite=200)
    if not interacoes:
        st.info("Nenhuma comunicação registrada ainda.")
        return

    hoje = datetime.datetime.now(APP_TZ).date()
    opcoes = {
        "Hoje": hoje,
        "Últimos 7 dias": hoje - datetime.timedelta(days=7),
        "Últimos 30 dias": hoje - datetime.timedelta(days=30),
        "Todo o histórico": None,
    }
    mapa_cat = {
        "Todos": None,
        "Emoções": "emocao",
        "Pedidos": "necessidade",
        "Ações": "acao",
    }

    col_f, col_cat, col_dl = st.columns([2, 2, 1])
    with col_f:
        filtro = st.selectbox("Período", list(opcoes.keys()), key="cui_periodo")
    with col_cat:
        cat_sel_lbl = st.selectbox("Tipo", list(mapa_cat.keys()), key="cui_cat")
    data_min = opcoes[filtro]

    if data_min == hoje:
        filtradas = [i for i in interacoes if str(i.get("registado_em", ""))[:10] == hoje.isoformat()]
    else:
        filtradas = [
            i
            for i in interacoes
            if not data_min or str(i.get("registado_em", ""))[:10] >= data_min.isoformat()
        ]
    cat_key = mapa_cat[cat_sel_lbl]
    if cat_key:
        filtradas = [i for i in filtradas if i.get("categoria") == cat_key]

    with col_dl:
        st.markdown('<div style="height:1.8rem"></div>', unsafe_allow_html=True)
        if filtradas:
            df_e = _formatar_exportacao(filtradas, crianca_nome)
            csv = df_e.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                "📥 Baixar",
                csv,
                f"historico_{safe_filename(nome_curto)}_{filename_date(hoje)}.csv",
                "text/csv",
                use_container_width=True,
            )

    if not filtradas:
        st.info("Nenhuma comunicação no período/tipo selecionado.")
        return

    st.caption(f"{len(filtradas)} comunicações no período")
    grupos: dict = {}
    for item in sorted(filtradas, key=lambda x: str(x.get("registado_em", "")), reverse=True):
        data_key = str(item.get("registado_em", ""))[:10]
        grupos.setdefault(data_key, []).append(item)

    dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    for data_str, items in grupos.items():
        try:
            data = datetime.date.fromisoformat(data_str)
            if data == hoje:
                label = f"Hoje · {len(items)} comunicações"
            elif data == hoje - datetime.timedelta(days=1):
                label = f"Ontem · {len(items)} comunicações"
            else:
                label = f"{dias_semana[data.weekday()]}, {format_date_br(data)} · {len(items)}"
        except Exception:
            label = f"{data_str} · {len(items)}"

        st.markdown(
            f'<div class="date-group">'
            f'  <span class="date-badge">📅 {label}</span>'
            f'  <div class="date-line"></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        for reg in items:
            cat = reg.get("categoria", "")
            hora = format_time(reg.get("registado_em"))
            emoji = reg.get("emoji", "")
            pict = reg.get("pictograma", "").title()
            badge_cls, badge_txt = BADGE_CAT.get(cat, ("badge-acao", cat))
            cor = COR_CAT.get(cat, "#6366f1")
            st.markdown(
                f'<div class="diary-item" style="border-left:3.5px solid {cor}">'
                f'  <span style="font-size:.75rem;color:#6b7280;min-width:2.8rem;font-weight:800">{hora}</span>'
                f'  <div class="diary-emoji">{emoji}</div>'
                f'  <div class="diary-name">{pict}</div>'
                f'  <span class="diary-badge {badge_cls}">{badge_txt}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


def _formatar_exportacao(registros: list[dict], crianca_nome: str) -> pd.DataFrame:
    df = pd.DataFrame(registros)
    exp = df[["registado_em", "pictograma", "categoria", "emoji"]].copy()
    exp["Criança"] = crianca_nome
    exp["Data/Hora"] = exp["registado_em"].apply(format_datetime_br)
    exp["Comunicação"] = exp["pictograma"].astype(str).str.title()
    exp["Tipo"] = exp["categoria"].astype(str).str.title()
    exp["Emoji"] = exp["emoji"]
    return exp[["Criança", "Data/Hora", "Comunicação", "Tipo", "Emoji"]]
