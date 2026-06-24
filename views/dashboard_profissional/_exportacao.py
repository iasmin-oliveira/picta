"""Export section for the professional dashboard."""

from __future__ import annotations

import datetime
import io

import pandas as pd
import streamlit as st

from modules.logs import APP_TZ, obter_interacoes_periodo
from utils.formatters import (
    filename_date,
    format_datetime_br,
    format_period_br,
    safe_filename,
)


def render_exportacao(crianca_id, crianca_nome: str) -> None:
    st.markdown(
        f'<div class="page-header">'
        f'  <div class="page-title">💾 Exportação</div>'
        f'  <div class="page-subtitle">'
        f'    Baixe dados clínicos de <b>{crianca_nome}</b> em CSV ou PDF.</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    hoje = datetime.datetime.now(APP_TZ).date()
    ini_key = f"exp_ini_{crianca_id}"
    fim_key = f"exp_fim_{crianca_id}"
    st.session_state.setdefault(ini_key, hoje - datetime.timedelta(days=30))
    st.session_state.setdefault(fim_key, hoje)

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        d_ini = st.date_input("De:", key=ini_key, format="DD/MM/YYYY")
    with col_d2:
        d_fim = st.date_input("Até:", key=fim_key, format="DD/MM/YYYY")

    if d_ini > d_fim:
        st.warning("A data inicial precisa ser anterior ou igual à data final.")
        return

    periodo_txt = format_period_br(d_ini, d_fim)
    st.caption(f"Período selecionado: {periodo_txt}")

    registos = obter_interacoes_periodo(crianca_id, d_ini, d_fim)
    if not registos:
        st.info("Sem dados no período selecionado.")
        return

    df = pd.DataFrame(registos)
    df["registado_em"] = pd.to_datetime(df["registado_em"])

    st.markdown(
        f'<div class="glass-card" style="text-align:center;padding:1.5rem;">'
        f'  <div style="font-size:2.2rem;font-weight:800;color:#1e1b4b">{len(df)}</div>'
        f'  <div style="font-size:.88rem;color:#6b7280;font-weight:700">'
        f'    registros prontos para exportar</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    export_df = _formatar_exportacao(df, crianca_nome)
    nome_base = safe_filename(crianca_nome)

    col_csv, col_pdf = st.columns(2)
    with col_csv:
        csv = export_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            "📥 Baixar CSV",
            csv,
            f"picta_{nome_base}_{filename_date(d_ini)}_{filename_date(d_fim)}.csv",
            "text/csv",
            use_container_width=True,
        )
    with col_pdf:
        pdf = _gerar_pdf(df, crianca_nome, d_ini, d_fim)
        st.download_button(
            "🖨️ Baixar PDF",
            pdf,
            f"relatorio_{nome_base}_{filename_date(d_ini)}_{filename_date(d_fim)}.pdf",
            "application/pdf",
            use_container_width=True,
        )


def _formatar_exportacao(df: pd.DataFrame, crianca_nome: str) -> pd.DataFrame:
    exp = df[["registado_em", "pictograma", "categoria", "emoji"]].copy()
    exp["Criança"] = crianca_nome
    exp["Data/Hora"] = exp["registado_em"].apply(format_datetime_br)
    exp["Pictograma"] = exp["pictograma"].astype(str).str.title()
    exp["Categoria"] = exp["categoria"].astype(str).str.title()
    exp["Emoji"] = exp["emoji"]
    return exp[["Criança", "Data/Hora", "Pictograma", "Categoria", "Emoji"]]


def _gerar_pdf(df: pd.DataFrame, nome: str, d1, d2) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )
        styles = getSampleStyleSheet()
        tit = ParagraphStyle(
            "T",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#4338ca"),
            alignment=TA_CENTER,
            spaceAfter=6,
        )
        sub = ParagraphStyle(
            "S",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#6b7280"),
            alignment=TA_CENTER,
            spaceAfter=12,
        )
        sec = ParagraphStyle(
            "Sec",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=colors.HexColor("#1e1b4b"),
            spaceBefore=14,
            spaceAfter=6,
        )

        elems = [
            Paragraph("PICTA - Relatório Clínico", tit),
            Paragraph(
                f"Paciente: <b>{nome}</b> | Período: {format_period_br(d1, d2)} | "
                f"Total: <b>{len(df)}</b> registros",
                sub,
            ),
            Spacer(1, 0.5 * cm),
        ]
        por_cat = df.groupby("categoria").size().reset_index(name="total")
        elems.append(Paragraph("Distribuição por Categoria", sec))
        tabela = [["Categoria", "Total", "%"]]
        for _, row in por_cat.iterrows():
            tabela.append(
                [
                    str(row["categoria"]).title(),
                    str(row["total"]),
                    f"{100 * row['total'] / len(df):.1f}%",
                ]
            )
        tbl = Table(tabela, colWidths=[6 * cm, 4 * cm, 4 * cm])
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4338ca")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#eef2ff"), colors.white]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e7ff")),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        elems += [tbl, Spacer(1, 0.5 * cm)]
        elems.append(
            Paragraph(
                f"Gerado em: {datetime.datetime.now(APP_TZ).strftime('%d/%m/%Y às %H:%M')} "
                "- PICTA - FACCAT 2026 - Apenas suporte clínico.",
                sub,
            )
        )
        doc.build(elems)
        return buf.getvalue()
    except ImportError:
        return b"%PDF-1.4\n% reportlab nao instalado"
