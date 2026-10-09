"""Interface de coleta controlada para o estudo de campo do PICTA."""

from __future__ import annotations

import os

import streamlit as st

FORMS_PROFISSIONAL_URL = "https://forms.gle/rpAzo45ttGTan8wA6"


def _obter_link_forms() -> str:
    try:
        cfg = st.secrets.get("pesquisa", {})
        if hasattr(cfg, "get") and cfg.get("forms_url"):
            return str(cfg.get("forms_url"))
    except Exception:
        pass
    return os.getenv("PICTA_FORMS_URL") or os.getenv("PESQUISA_FORMS_URL") or FORMS_PROFISSIONAL_URL


def _render_link_forms() -> None:
    forms_url = _obter_link_forms()
    st.markdown(
        '<div class="dashboard-orientation-card">'
        '<div class="dashboard-orientation-title">Pesquisa externa</div>'
        '<div class="dashboard-orientation-text">'
        'Use o formulário externo para TCLE e avaliação do profissional. '
        'O registro das respostas da pesquisa fica centralizado no Google Forms.'
        '</div></div>',
        unsafe_allow_html=True,
    )
    st.link_button("Abrir formulário do profissional", forms_url, use_container_width=False)


def render() -> None:
    st.markdown("## 🧪 Coleta de pesquisa")
    st.caption(
        "Acesso ao formulário do profissional usado no TCC e na avaliação do PICTA."
    )
    _render_link_forms()
