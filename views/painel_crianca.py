"""Child communication panel."""

from __future__ import annotations

import html
import json
import time

import streamlit as st
import streamlit.components.v1 as components

from database.db import executar, garantir_pictogramas_seed
from modules.logs import registar_interacao
from utils.css_loader import inject_css
from utils.debug_logger import log_debug
from utils.security import criar_ou_obter_crianca_do_usuario

CATEGORIAS = {
    "emocao": {"label": "Como me sinto", "emoji": "💜", "hint": "Escolha um sentimento"},
    "acao": {"label": "O que quero fazer", "emoji": "💙", "hint": "Escolha uma ação"},
    "necessidade": {"label": "O que preciso", "emoji": "💚", "hint": "Escolha um pedido"},
}
CATEGORIA_ORDEM = ["emocao", "acao", "necessidade"]
CATEGORIA_FEEDBACK = {"emocao": "Sentimento", "acao": "Ação", "necessidade": "Necessidade"}
CATEGORIA_FALA = {"emocao": "Sentimento", "acao": "O que quero fazer", "necessidade": "Necessidade"}
ORIENTACAO_TITULO = "Como usar o PICTA"
ORIENTACAO_TEXTO = (
    "Escolha uma categoria: como me sinto, o que quero fazer ou o que preciso. "
    "Depois toque em uma figura. Eu vou falar a sua escolha e salvar para o seu "
    "responsavel e profissional acompanharem."
)
ORIENTACAO_FALA = (
    "Oi! Eu sou o PICTA. Primeiro escolha uma categoria: como me sinto, "
    "o que quero fazer, ou o que preciso. Depois toque em uma figura. "
    "Eu vou falar a sua escolha e salvar para o seu responsavel e profissional acompanharem. "
    "Se quiser ouvir esta explicacao de novo, toque no botao ajuda."
)


def _obter_pictogramas() -> dict:
    garantir_pictogramas_seed()
    rows = executar("SELECT MIN(id) AS id, nome, categoria, MAX(emoji) AS emoji FROM Pictogramas GROUP BY nome, categoria ORDER BY categoria, nome", fetchall=True) or []
    pictogramas: dict = {}
    for row in rows:
        pictogramas.setdefault(row["categoria"], []).append({"id": row["id"], "nome": row["nome"], "emoji": row["emoji"], "categoria": row["categoria"]})
    return pictogramas


def render() -> None:
    usuario = st.session_state.get("usuario") or {}
    usuario_id = usuario.get("id")
    nome = usuario.get("nome", "Criança")
    primeiro = nome.split()[0] if nome else "Criança"
    if not usuario_id:
        st.warning("Faça login para acessar o PICTA.")
        st.stop()
    if _query_valor("pc_logout"):
        from controllers.auth_controller import logout
        logout()

    crianca_cache_key = f"pc_crianca_id_{usuario_id}"
    crianca_id = st.session_state.get(crianca_cache_key) or usuario.get("crianca_id")
    if not crianca_id:
        crianca_id = criar_ou_obter_crianca_do_usuario(usuario_id, nome)
        if crianca_id:
            st.session_state[crianca_cache_key] = crianca_id
            st.session_state.setdefault("usuario", {})["crianca_id"] = crianca_id
    elif crianca_cache_key not in st.session_state:
        st.session_state[crianca_cache_key] = crianca_id
    if not crianca_id:
        st.error("Não foi possível carregar o painel da criança.")
        st.stop()

    inject_css("painel_crianca_grid.css")
    pictos_por_cat = _obter_pictogramas()
    categorias = [cat for cat in CATEGORIA_ORDEM if pictos_por_cat.get(cat)]
    if not categorias:
        st.info("Nenhum pictograma cadastrado ainda.")
        return
    _render_header(primeiro)
    _render_orientacao(crianca_id)
    feedback_slot = st.empty()
    feedback = st.session_state.get("pc_feedback")
    feedback_until = st.session_state.get("pc_feedback_until", 0)
    if feedback and time.time() < feedback_until:
        _mostrar_feedback(feedback_slot, feedback["emoji"], feedback["nome"], feedback["categoria"])
    else:
        st.session_state.pop("pc_feedback", None)
        st.session_state.pop("pc_feedback_until", None)
    erro = st.session_state.pop("pc_registro_erro", "")
    if erro:
        feedback_slot.error(erro)
    fala = st.session_state.pop("pc_fala_pendente", "")
    if fala:
        _falar(fala)
    _render_paineis_categoria(categorias, pictos_por_cat, crianca_id)


def _render_header(primeiro: str) -> None:
    primeiro_html = html.escape(primeiro)
    st.markdown(f'<div class="pc-header"><div class="pc-header-copy"><div class="pc-saudacao">Ol&aacute;, {primeiro_html}!</div><div class="pc-sub">Como voc&ecirc; est&aacute; se sentindo agora?</div></div><div class="pc-header-actions"><div class="pc-header-icon">&#127752;</div><a class="pc-logout-link" href="?pc_logout=1" target="_self">Sair</a></div></div>', unsafe_allow_html=True)


def _render_orientacao(crianca_id: int) -> None:
    concluida_key = f"pc_orientacao_concluida_{crianca_id}"
    falada_key = f"pc_orientacao_falada_{crianca_id}"
    if st.session_state.get(concluida_key) or _crianca_tem_interacoes(crianca_id):
        st.session_state[concluida_key] = True
        _render_botao_ajuda("Ajuda")
        return

    if not st.session_state.get(falada_key):
        st.session_state[falada_key] = True
        _falar(ORIENTACAO_FALA)

    st.markdown(
        '<div class="pc-orientacao">'
        '<div class="pc-orientacao-ico">&#128266;</div>'
        '<div class="pc-orientacao-copy">'
        f'<div class="pc-orientacao-titulo">{html.escape(ORIENTACAO_TITULO)}</div>'
        f'<div class="pc-orientacao-texto">{html.escape(ORIENTACAO_TEXTO)}</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    _render_botao_ajuda("Ouvir ajuda")


def _crianca_tem_interacoes(crianca_id: int) -> bool:
    try:
        row = executar(
            "SELECT 1 FROM Registos_Interacao WHERE crianca_id = ? LIMIT 1",
            (crianca_id,),
            fetchone=True,
        )
        return bool(row)
    except Exception as exc:
        log_debug(f"erro_verificar_primeira_interacao crianca={crianca_id}: {exc}")
        return False


def _render_botao_ajuda(label: str) -> None:
    label_payload = json.dumps(label, ensure_ascii=False)
    texto_payload = json.dumps(ORIENTACAO_FALA, ensure_ascii=False)
    components.html(
        f"""
<button id="pc-help-button" type="button" aria-label={label_payload}>🔊 {html.escape(label)}</button>
<style>
  #pc-help-button {{
    width: 100%;
    min-height: 46px;
    border: 2px solid #E0D6FF;
    border-radius: 12px;
    background: #ffffff;
    color: #2D2145;
    font: 800 0.92rem "Segoe UI", system-ui, sans-serif;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(107,79,160,0.06);
  }}
  #pc-help-button:hover, #pc-help-button:focus {{
    border-color: #6B4FA0;
    color: #6B4FA0;
    outline: none;
  }}
</style>
<script>
(() => {{
  const texto = {texto_payload};
  const botao = document.getElementById("pc-help-button");
  if (!botao) return;
  botao.addEventListener("click", () => {{
    try {{
      const w = window.parent || window;
      const synth = w.speechSynthesis || window.speechSynthesis;
      if (!synth) return;
      synth.cancel();
      const fala = new SpeechSynthesisUtterance(texto);
      fala.lang = "pt-BR";
      fala.rate = 0.9;
      fala.pitch = 1.05;
      w.__pictaLastSpoken = {{ texto, ts: Date.now() }};
      synth.speak(fala);
    }} catch (err) {{}}
  }});
}})();
</script>
""",
        height=54,
    )


def _render_paineis_categoria(categorias: list[str], pictos_por_cat: dict, crianca_id: int) -> None:
    if "pc_categoria" not in st.session_state or st.session_state["pc_categoria"] not in categorias:
        st.session_state["pc_categoria"] = categorias[0]

    labels = [f'{CATEGORIAS[cat]["emoji"]} {CATEGORIAS[cat]["label"]}' for cat in categorias]
    valor_atual = f'{CATEGORIAS[st.session_state["pc_categoria"]]["emoji"]} {CATEGORIAS[st.session_state["pc_categoria"]]["label"]}'
    escolhido = st.radio(
        "Categorias",
        labels,
        index=labels.index(valor_atual),
        horizontal=True,
        label_visibility="collapsed",
    )
    categoria = categorias[labels.index(escolhido)]
    st.session_state["pc_categoria"] = categoria

    info = CATEGORIAS[categoria]
    st.markdown(f'<div class="pc-panel-hint">{html.escape(info["hint"])}</div>', unsafe_allow_html=True)
    pictogramas = pictos_por_cat[categoria]
    for linha in range(0, len(pictogramas), 4):
        cols = st.columns(4)
        for col, picto in zip(cols, pictogramas[linha:linha + 4]):
            nome = str(picto["nome"]).title()
            label = f'{picto["emoji"]}\n{nome}'
            with col:
                if st.button(label, key=f'pc_botao_pictograma_{picto["id"]}', use_container_width=True):
                    _processar_clique_pictograma(crianca_id, picto)


def _processar_clique_pictograma(crianca_id: int, picto: dict) -> None:
    picto_id = int(picto["id"])
    categoria = str(picto.get("categoria", ""))
    nome = str(picto.get("nome", "")).title()
    if _registrar_interacao(crianca_id, picto_id):
        st.session_state[f"pc_orientacao_concluida_{crianca_id}"] = True
        st.session_state["pc_feedback"] = {
            "emoji": picto.get("emoji", ""),
            "nome": nome,
            "categoria": categoria,
        }
        st.session_state["pc_feedback_until"] = time.time() + 4
        st.session_state["pc_categoria"] = categoria
        categoria_label = CATEGORIA_FEEDBACK.get(categoria, "Registro")
        st.session_state["pc_fala_pendente"] = f"{CATEGORIA_FALA.get(categoria, categoria_label)}: {nome}"
    else:
        st.session_state["pc_registro_erro"] = "Não consegui salvar esta escolha. Faça login novamente e tente outra vez."
    st.rerun()


def _registrar_interacao(crianca_id: int, pictograma_id: int) -> bool:
    ok = registar_interacao(crianca_id=crianca_id, pictograma_id=pictograma_id)
    log_debug(f"pictograma={pictograma_id} registrado={ok}")
    return ok


def _mostrar_feedback(slot, emoji: str, nome: str, categoria: str) -> None:
    categoria_label = CATEGORIA_FEEDBACK.get(categoria, "Registro")
    slot.markdown(f'<div class="pc-feedback-top"><span class="pc-feedback-emoji">{html.escape(str(emoji))}</span><span class="pc-feedback-text"><b>{html.escape(nome)}</b> registrado.<small>{html.escape(categoria_label)}</small></span></div>', unsafe_allow_html=True)


def _query_valor(nome: str) -> str:
    valor = st.query_params.get(nome)
    if isinstance(valor, list):
        return valor[0] if valor else ""
    return str(valor or "")


def _falar(texto: str) -> None:
    payload = json.dumps(texto, ensure_ascii=False)
    components.html(f"""<script>(() => {{ const texto = {payload}; try {{ const w = window.parent || window; const ultimo = w.__pictaLastSpoken || {{}}; if (ultimo.texto === texto && Date.now() - ultimo.ts < 5000) return; const synth = w.speechSynthesis || window.speechSynthesis; if (!synth) return; synth.cancel(); const fala = new SpeechSynthesisUtterance(texto); fala.lang = 'pt-BR'; fala.rate = 0.9; fala.pitch = 1.05; w.__pictaLastSpoken = {{ texto, ts: Date.now() }}; synth.speak(fala); }} catch (err) {{}} }})();</script>""", height=1)


log_debug("painel_crianca.py carregado")
