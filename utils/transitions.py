"""
PICTA — utils/transitions.py

CSS global de transições limpas entre telas do Streamlit.

O que foi REMOVIDO vs versão anterior:
  ✗ Overlay [data-stale="true"] com visibility:hidden → era a causa do "fantasma"
  ✗ ::before / ::after com fundo roxo → causava flash colorido em cada rerun
  ✗ JS via components.html → zero necessidade aqui
  ✗ Toast JS manual → st.toast() nativo é suficiente

O que PERMANECE:
  ✓ Ocultação de elementos nativos do Streamlit que poluem a UI
  ✓ Fade-in 120ms na troca de tela — suave, sem impacto visual
  ✓ Padding ajustado para telas de app
"""

import streamlit as st

_CSS = """
<style>
/* ── Oculta poluição nativa do Streamlit ── */
[data-testid="stSpinner"],
[data-testid="stStatusWidget"],
[data-testid="stDeployButton"],
[data-testid="stToolbar"],
footer, #MainMenu { display: none !important; }

/* ── Fade suave na troca de tela (rerun) ── */
[data-testid="stAppViewContainer"] {
    animation: st-fadein 0.12s ease-out both;
}
@keyframes st-fadein { from { opacity: 0.55; } to { opacity: 1; } }

/* ── Padding padrão para telas de app ── */
[data-testid="stAppViewBlockContainer"] {
    padding-top: 0.5rem !important;
    padding-bottom: 1rem !important;
}

/* ── Foco visual limpo ── */
button:focus-visible {
    outline: 3px solid #7B4FA6 !important;
    outline-offset: 2px !important;
    box-shadow: none !important;
}
button:focus:not(:focus-visible) {
    outline: none !important;
    box-shadow: none !important;
}
</style>
"""


def inject_transition_system() -> None:
    """
    Injeta CSS de transição limpa.
    Chamar no início do render() de cada tela.
    Sem JS, sem overlay, sem efeito fantasma.
    """
    st.markdown(_CSS, unsafe_allow_html=True)


def toast_js(emoji: str, nome: str, ok: bool = True) -> None:
    """
    Wrapper de st.toast() — mantido por compatibilidade com chamadas existentes.
    Zero JS, zero rerender adicional.
    """
    if ok:
        st.toast(f'{emoji} {nome} registado!', icon='✅')
    else:
        st.toast('⚠️ Algo correu mal. Tenta novamente.')