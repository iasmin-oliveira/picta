"""Fast insights for the professional dashboard."""

from __future__ import annotations

import datetime
import html

import altair as alt
import pandas as pd
import streamlit as st

from modules.logs import APP_TZ, obter_interacoes_periodo
from utils.formatters import filename_date, format_period_br, safe_filename
from ._constants import EMOCOES_ALERTA, EMOCOES_POSITIVAS, PESO_EMOCAO


def render_insights(crianca_id, crianca_nome: str) -> None:
    st.markdown(
        f'<div class="page-header">'
        f'  <div class="page-title">🔬 Insights</div>'
        f'  <div class="page-subtitle">'
        f'    Leitura rápida dos padrões de comunicação de <b>{html.escape(crianca_nome)}</b>.</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    hoje = datetime.datetime.now(APP_TZ).date()
    ini_key = f"ia_ini_{crianca_id}"
    fim_key = f"ia_fim_{crianca_id}"
    st.session_state.setdefault(ini_key, hoje - datetime.timedelta(days=30))
    st.session_state.setdefault(fim_key, hoje)

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        d_ini = st.date_input("De:", key=ini_key, format="DD/MM/YYYY")
    with col_d2:
        d_fim = st.date_input("Até:", key=fim_key, format="DD/MM/YYYY")

    if d_ini > d_fim:
        st.error("A data inicial precisa ser menor ou igual à data final.")
        return

    periodo_txt = format_period_br(d_ini, d_fim)
    st.caption(f"Período analisado: {periodo_txt}")

    registos = obter_interacoes_periodo(crianca_id, d_ini, d_fim)
    if not registos:
        st.info("Sem interações no período selecionado.")
        return

    df = _preparar_dataframe(registos)
    df_em = df[df["categoria"] == "emocao"].copy()
    score = _score_bem_estar(df_em)
    top = df["pictograma"].value_counts()
    top_nome = str(top.index[0]).title() if not top.empty else "-"
    hora_pico = int(df["hora"].value_counts().idxmax()) if not df.empty else 0
    dias = max(df["data"].nunique(), 1)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interações", len(df))
    c2.metric("Dias ativos", dias)
    c3.metric("Bem-estar", f"{score:.1f}/10")
    c4.metric("Pico", f"{hora_pico:02d}h")

    st.markdown(
        f'<div class="ia-hero">'
        f'  <div class="ia-hero-title">Resumo do período</div>'
        f'  <div class="ia-hero-text">{html.escape(_resumo(score, top_nome, hora_pico))}</div>'
        f'  <div class="ia-suggestion">'
        f'    <div class="ia-suggestion-label">Sugestão de acompanhamento</div>'
        f'    <div class="ia-suggestion-text">{html.escape(_sugestao(df, df_em, score, hora_pico))}</div>'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="chart-label">Comunicações por dia</div>', unsafe_allow_html=True)
        diario = df.groupby(["data", "categoria_rotulo"], as_index=False).agg(total=("id", "count"))
        diario_chart = (
            alt.Chart(diario)
            .mark_line(point=True)
            .encode(
                x=alt.X("data:T", title="", axis=alt.Axis(format="%d/%m", labelAngle=0)),
                y=alt.Y("total:Q", title="", scale=alt.Scale(zero=True)),
                color=alt.Color(
                    "categoria_rotulo:N",
                    title="Categoria",
                    sort=["Ação", "Emoção", "Necessidade", "Outros"],
                ),
                tooltip=[
                    alt.Tooltip("data:T", title="Data", format="%d/%m/%Y"),
                    alt.Tooltip("categoria_rotulo:N", title="Categoria"),
                    alt.Tooltip("total:Q", title="Interações"),
                ],
            )
            .properties(height=260)
        )
        st.altair_chart(diario_chart, use_container_width=True)

        st.markdown('<div class="chart-label">Itens mais usados</div>', unsafe_allow_html=True)
        top_itens = df["pictograma"].str.title().value_counts().head(8).sort_values()
        st.bar_chart(top_itens, use_container_width=True)

    with col_b:
        st.markdown('<div class="chart-label">Bem-estar por dia</div>', unsafe_allow_html=True)
        score_dia = _score_por_dia(df_em)
        if score_dia.empty:
            st.caption("Ainda não há emoções suficientes para pontuar o período.")
        else:
            score_chart = (
                alt.Chart(score_dia)
                .mark_line(point=True)
                .encode(
                    x=alt.X("data:T", title="", axis=alt.Axis(format="%d/%m", labelAngle=0)),
                    y=alt.Y("score:Q", title="", scale=alt.Scale(domain=[0, 10])),
                    tooltip=[
                        alt.Tooltip("data:T", title="Data", format="%d/%m/%Y"),
                        alt.Tooltip("score:Q", title="Bem-estar", format=".1f"),
                    ],
                )
                .properties(height=260)
            )
            st.altair_chart(score_chart, use_container_width=True)

        st.markdown('<div class="chart-label">Horários de uso</div>', unsafe_allow_html=True)
        horas = df.groupby("hora").size().reindex(range(24), fill_value=0)
        horas.index = [f"{h:02d}h" for h in horas.index]
        st.bar_chart(horas, use_container_width=True)

    _render_alertas(df, df_em)
    _render_relatorio(df, df_em, crianca_nome, d_ini, d_fim, score)


def _preparar_dataframe(registos: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(registos)
    df["registado_em"] = pd.to_datetime(df["registado_em"])
    df["data"] = df["registado_em"].dt.date
    df["data_label"] = df["data"].apply(lambda d: f"{d.day:02d}/{d.month:02d}")
    df["hora"] = df["registado_em"].dt.hour
    df["categoria"] = df["categoria"].fillna("outros")
    df["categoria_rotulo"] = df["categoria"].map(
        {
            "acao": "Ação",
            "emocao": "Emoção",
            "necessidade": "Necessidade",
            "outros": "Outros",
        }
    ).fillna(df["categoria"].str.title())
    return df


def _score_bem_estar(df_em: pd.DataFrame) -> float:
    if df_em.empty:
        return 5.0
    pesos = df_em["pictograma"].map(PESO_EMOCAO).fillna(0)
    return float(((pesos.mean() + 1) / 2 * 10).clip(0, 10))


def _score_por_dia(df_em: pd.DataFrame) -> pd.DataFrame:
    if df_em.empty:
        return pd.DataFrame(columns=["data", "score"])
    df = df_em.copy()
    df["peso"] = df["pictograma"].map(PESO_EMOCAO).fillna(0)
    score = ((df.groupby("data")["peso"].mean() + 1) / 2 * 10).clip(0, 10)
    return score.round(1).rename("score").reset_index()


def _resumo(score: float, top_nome: str, hora_pico: int) -> str:
    if score >= 6.5:
        tom = "predomínio de emoções positivas"
    elif score >= 4.5:
        tom = "equilíbrio entre emoções positivas e sinais de atenção"
    else:
        tom = "maior presença de sinais de atenção"
    return f"O período mostra {tom}. O item mais frequente foi {top_nome}, e o horário de maior uso foi {hora_pico:02d}h."


def _sugestao(df: pd.DataFrame, df_em: pd.DataFrame, score: float, hora_pico: int) -> str:
    necessidades = df[df["categoria"] == "necessidade"]["pictograma"].value_counts()
    if not necessidades.empty:
        top = str(necessidades.index[0]).lower()
        return f"Observe se '{top}' aparece perto de {hora_pico:02d}h e antecipe esse recurso na rotina."
    if score < 4.5:
        return "Priorize estratégias de regulação e observe contexto, ruído, sono e transições antes dos horários de pico."
    if not df_em.empty:
        top_em = str(df_em["pictograma"].value_counts().index[0]).lower()
        return f"Use atividades de reforço quando a emoção '{top_em}' aparecer associada a boa participação."
    return "Continue registrando para formar uma linha de base clínica mais clara."


def _render_alertas(df: pd.DataFrame, df_em: pd.DataFrame) -> None:
    alertas = []
    if not df_em.empty:
        pct_alerta = 100 * df_em["pictograma"].isin(EMOCOES_ALERTA).mean()
        if pct_alerta >= 50:
            alertas.append(f"{pct_alerta:.0f}% das emoções registradas são sinais de atenção.")

    noturnos = int(((df["hora"] >= 23) | (df["hora"] <= 5)).sum())
    if noturnos:
        alertas.append(f"{noturnos} interação(ões) ocorreram entre 23h e 5h.")

    ajuda = int((df["pictograma"] == "AJUDA").sum())
    if ajuda >= 2:
        alertas.append(f"'AJUDA' foi selecionada {ajuda} vezes no período.")

    st.markdown('<div class="chart-label">Pontos de atenção</div>', unsafe_allow_html=True)
    if not alertas:
        st.markdown('<div class="ok-card">Nenhum ponto crítico detectado no período.</div>', unsafe_allow_html=True)
        return

    for alerta in alertas:
        st.markdown(f'<div class="alert-card">{html.escape(alerta)}</div>', unsafe_allow_html=True)


def _render_relatorio(
    df: pd.DataFrame,
    df_em: pd.DataFrame,
    nome: str,
    d_ini,
    d_fim,
    score: float,
) -> None:
    cat = df["categoria"].value_counts().to_dict()
    positivas = int(df_em["pictograma"].isin(EMOCOES_POSITIVAS).sum()) if not df_em.empty else 0
    atencao = int(df_em["pictograma"].isin(EMOCOES_ALERTA).sum()) if not df_em.empty else 0
    top = df["pictograma"].str.title().value_counts().head(5)
    necessidades = df[df["categoria"] == "necessidade"]["pictograma"].str.title().value_counts().head(3)
    acoes = df[df["categoria"] == "acao"]["pictograma"].str.title().value_counts().head(3)
    hora_pico = int(df["hora"].value_counts().idxmax()) if not df.empty else 0
    dias_ativos = int(df["data"].nunique())
    noturnos = int(((df["hora"] >= 23) | (df["hora"] <= 5)).sum())
    periodo_txt = format_period_br(d_ini, d_fim)
    total = len(df)
    total_emocoes = max(len(df_em), 1)
    positivas_pct = positivas / total_emocoes * 100
    atencao_pct = atencao / total_emocoes * 100
    top_txt = ", ".join(f"{item} ({qtd})" for item, qtd in top.items()) or "Sem destaque"
    necessidades_txt = ", ".join(f"{item} ({qtd})" for item, qtd in necessidades.items()) or "Sem pedidos no período"
    acoes_txt = ", ".join(f"{item} ({qtd})" for item, qtd in acoes.items()) or "Sem ações no período"
    categoria_txt = (
        f"emoção={cat.get('emocao', 0)}, "
        f"ação={cat.get('acao', 0)}, "
        f"necessidade={cat.get('necessidade', 0)}"
    )
    recomendacao = _sugestao(df, df_em, score, hora_pico)

    linhas = [
        "PICTA - Relatório de insights",
        f"Paciente: {nome}",
        f"Período: {periodo_txt}",
        f"Total de interações: {total}",
        f"Dias ativos: {dias_ativos}",
        f"Score de bem-estar: {score:.1f}/10",
        f"Emoções positivas: {positivas} ({positivas_pct:.0f}%)",
        f"Emoções de atenção: {atencao} ({atencao_pct:.0f}%)",
        f"Horário de maior uso: {hora_pico:02d}h",
        f"Registros entre 23h e 5h: {noturnos}",
        f"Por categoria: {categoria_txt}",
        f"Mais frequentes: {top_txt}",
        f"Pedidos recorrentes: {necessidades_txt}",
        f"Ações recorrentes: {acoes_txt}",
        f"Sugestão: {recomendacao}",
    ]
    relatorio = "\n".join(linhas)

    resumo_html = (
        '<details class="picta-details picta-summary-details">'
        '  <summary><span>Ver resumo textual</span><small>Síntese clínica do período</small></summary>'
        '  <div class="picta-summary-body">'
        f'    <p><b>{html.escape(nome)}</b> teve <b>{total}</b> comunicações em '
        f'    <b>{dias_ativos}</b> dia(s) ativo(s), com bem-estar estimado em '
        f'    <b>{score:.1f}/10</b>.</p>'
        '    <div class="picta-summary-grid">'
        f'      <div><strong>Emoções</strong><span>{positivas_pct:.0f}% positivas · {atencao_pct:.0f}% atenção</span></div>'
        f'      <div><strong>Horário</strong><span>Pico às {hora_pico:02d}h · {noturnos} registro(s) noturno(s)</span></div>'
        f'      <div><strong>Mais usados</strong><span>{html.escape(top_txt)}</span></div>'
        f'      <div><strong>Pedidos</strong><span>{html.escape(necessidades_txt)}</span></div>'
        f'      <div><strong>Ações</strong><span>{html.escape(acoes_txt)}</span></div>'
        f'      <div><strong>Acompanhamento</strong><span>{html.escape(recomendacao)}</span></div>'
        '    </div>'
        '  </div>'
        '</details>'
    )
    st.markdown(resumo_html, unsafe_allow_html=True)
    st.download_button(
        "Baixar resumo (.txt)",
        relatorio.encode("utf-8"),
        f"insights_{safe_filename(nome)}_{filename_date(d_ini)}_{filename_date(d_fim)}.txt",
        "text/plain",
        use_container_width=True,
    )
