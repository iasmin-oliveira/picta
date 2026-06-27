"""Child communication panel."""

from __future__ import annotations

import html
import json
import threading
import time
from urllib.parse import urlencode

import streamlit as st
import streamlit.components.v1 as components

from database.db import executar
from modules.auth import obter_ou_criar_crianca
from modules.logs import registar_interacao
from utils.css_loader import inject_css
from utils.debug_logger import log_debug

CATEGORIAS = {
    "emocao": {
        "label": "Como me sinto",
        "emoji": "💜",
        "hint": "Escolha um sentimento",
    },
    "acao": {
        "label": "O que quero fazer",
        "emoji": "💙",
        "hint": "Escolha uma ação",
    },
    "necessidade": {
        "label": "O que preciso",
        "emoji": "💚",
        "hint": "Escolha um pedido",
    },
}
CATEGORIA_ORDEM = ["emocao", "acao", "necessidade"]
CATEGORIA_FEEDBACK = {
    "emocao": "Sentimento",
    "acao": "Ação",
    "necessidade": "Necessidade",
}
CATEGORIA_FALA = {
    "emocao": "Sentimento",
    "acao": "O que quero fazer",
    "necessidade": "Necessidade",
}


@st.cache_data(ttl=300)
def _obter_pictogramas() -> dict:
    rows = executar(
        "SELECT MIN(id) AS id, nome, categoria, MAX(emoji) AS emoji "
        "FROM Pictogramas "
        "GROUP BY nome, categoria "
        "ORDER BY categoria, nome",
        fetchall=True,
    ) or []

    pictogramas: dict = {}
    for row in rows:
        pictogramas.setdefault(row["categoria"], []).append(
            {
                "id": row["id"],
                "nome": row["nome"],
                "emoji": row["emoji"],
                "categoria": row["categoria"],
            }
        )
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
    crianca_id = st.session_state.get(crianca_cache_key)
    if not crianca_id:
        crianca_id = obter_ou_criar_crianca(usuario_id, nome)
        if crianca_id:
            st.session_state[crianca_cache_key] = crianca_id
    if not crianca_id:
        st.error("Não foi possível carregar o painel da criança.")
        st.stop()

    inject_css("painel_crianca_grid.css")
    _instalar_feedback_cliente()
    _instalar_fala_cliente()

    pictos_por_cat = _obter_pictogramas()
    categorias = [cat for cat in CATEGORIA_ORDEM if pictos_por_cat.get(cat)]
    if not categorias:
        st.info("Nenhum pictograma cadastrado ainda.")
        return

    _processar_pictograma_query(crianca_id, pictos_por_cat)

    _render_header(primeiro)

    feedback_slot = st.empty()
    feedback = st.session_state.get("pc_feedback")
    feedback_until = st.session_state.get("pc_feedback_until", 0)
    if feedback and time.time() < feedback_until:
        _mostrar_feedback(feedback_slot, feedback["emoji"], feedback["nome"], feedback["categoria"])
    else:
        st.session_state.pop("pc_feedback", None)
        st.session_state.pop("pc_feedback_until", None)
    _render_paineis_categoria(categorias, pictos_por_cat)
    st.markdown(
        '<iframe class="pc-register-frame" name="pc-register-frame" '
        'title="Registro de comunicação"></iframe>',
        unsafe_allow_html=True,
    )


def _render_header(primeiro: str) -> None:
    primeiro_html = html.escape(primeiro)
    col_info, col_sair = st.columns([5, 1])

    with col_info:
        st.markdown(
            f'<div class="pc-header">'
            f'  <div>'
            f'    <div class="pc-saudacao">Olá, {primeiro_html}!</div>'
            f'    <div class="pc-sub">Como você está se sentindo agora?</div>'
            f'  </div>'
            f'  <div class="pc-header-icon">🌈</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_sair:
        st.markdown(
            '<a class="pc-logout-link" href="?pc_logout=1" target="_self">Sair</a>',
            unsafe_allow_html=True,
        )


def _render_paineis_categoria(categorias: list[str], pictos_por_cat: dict) -> None:
    if "pc_categoria" not in st.session_state or st.session_state["pc_categoria"] not in categorias:
        st.session_state["pc_categoria"] = categorias[0]

    atual = st.session_state["pc_categoria"]
    links = []
    paineis = []
    for cat in categorias:
        info = CATEGORIAS[cat]
        tab_id = f"pc-tab-{cat}"
        classe = "pc-cat-tab pc-cat-default" if cat == atual else "pc-cat-tab"
        painel_classe = "pc-painel pc-default-panel" if cat == atual else "pc-painel"
        links.append(
            f'<a class="{classe}" href="#{tab_id}" aria-label="{html.escape(info["label"])}">'
            f'  <span class="tab-ico">{html.escape(info["emoji"])}</span>'
            f'  <span>{html.escape(info["label"])}</span>'
            f'</a>'
        )
        paineis.append(
            f'<section id="{tab_id}" class="{painel_classe}">'
            f'  <div class="pc-panel-hint">{html.escape(info["hint"])}</div>'
            f'  <div class="pc-native-grid">{_render_grid_html(pictos_por_cat[cat])}</div>'
            f'</section>'
        )

    st.markdown(
        '<div class="pc-tabs">'
        '<nav class="pc-cat-menu" aria-label="Categorias">'
        + "".join(links)
        + "</nav>"
        + "".join(paineis)
        + "</div>",
        unsafe_allow_html=True,
    )


def _render_grid_html(pictogramas: list[dict]) -> str:
    nonce = str(time.time_ns())
    cards = []

    for picto in pictogramas:
        nome = picto["nome"].title()
        categoria = str(picto.get("categoria", ""))
        categoria_label = {
            "emocao": "Sentimento",
            "acao": "Ação",
            "necessidade": "Necessidade",
        }.get(categoria, "Registro")
        categoria_label = CATEGORIA_FEEDBACK.get(categoria, categoria_label)
        fala_texto = f'{CATEGORIA_FALA.get(categoria, categoria_label)}: {nome}'
        feedback_payload = html.escape(
            json.dumps(
                {
                    "emoji": str(picto["emoji"]),
                    "nome": nome,
                    "categoria": categoria_label,
                    "fala": fala_texto,
                },
                ensure_ascii=False,
            ),
            quote=True,
        )
        params = urlencode(
            {
                "pc_picto": str(picto["id"]),
                "pc_cat": categoria,
                "pc_nonce": nonce,
            }
        )
        cards.append(
            f'<a class="pc-picto-button" href="?{params}" target="pc-register-frame" '
            f'aria-label="{html.escape(nome)}" data-feedback="{feedback_payload}">'
            f'  <span class="pc-picto-emoji">{html.escape(str(picto["emoji"]))}</span>'
            f'  <span class="pc-picto-name">{html.escape(nome)}</span>'
            f'  <span class="pc-card-feedback" aria-hidden="true">'
            f'    <span class="pc-feedback-emoji">{html.escape(str(picto["emoji"]))}</span>'
            f'    <span class="pc-feedback-text">'
            f'      <b>{html.escape(nome)}</b> registrado.'
            f'      <small>{html.escape(categoria_label)}</small>'
            f'    </span>'
            f'  </span>'
            f'</a>'
        )

    return "".join(cards)


def _processar_pictograma_query(crianca_id: int, pictos_por_cat: dict) -> None:
    picto_raw = _query_valor("pc_picto")
    if not picto_raw:
        return

    nonce = _query_valor("pc_nonce") or ""
    chave = f"{picto_raw}:{nonce}"
    if st.session_state.get("_pc_ultimo_registro_query") == chave:
        _limpar_query_params()
        st.rerun()
        return

    try:
        picto_id = int(picto_raw)
    except (TypeError, ValueError):
        _limpar_query_params()
        st.rerun()
        return

    picto = _buscar_pictograma(pictos_por_cat, picto_id)
    if not picto:
        _limpar_query_params()
        st.rerun()
        return

    _registrar_interacao_assincrona(crianca_id, picto_id)
    st.session_state["_pc_ultimo_registro_query"] = chave

    feedback = {
        "emoji": picto["emoji"],
        "nome": picto["nome"].title(),
        "categoria": picto.get("categoria", ""),
    }
    st.session_state["pc_feedback"] = feedback
    st.session_state["pc_feedback_until"] = time.time() + 4
    if feedback["categoria"] in CATEGORIAS:
        st.session_state["pc_categoria"] = feedback["categoria"]

    _limpar_query_params()
    st.rerun()


def _buscar_pictograma(pictos_por_cat: dict, picto_id: int) -> dict | None:
    for pictos in pictos_por_cat.values():
        for picto in pictos:
            if int(picto["id"]) == picto_id:
                return picto
    return None


def _registrar_interacao_assincrona(crianca_id: int, pictograma_id: int) -> None:
    def worker() -> None:
        try:
            ok = registar_interacao(crianca_id=crianca_id, pictograma_id=pictograma_id)
            log_debug(f"pictograma={pictograma_id} registrado={ok}")
        except Exception as exc:
            log_debug(f"erro_registro_pictograma={pictograma_id}: {exc}")

    threading.Thread(target=worker, name="picta-registro-interacao", daemon=True).start()


def _mostrar_feedback(slot, emoji: str, nome: str, categoria: str) -> None:
    categoria_label = {
        "emocao": "Sentimento",
        "acao": "Ação",
        "necessidade": "Necessidade",
    }.get(categoria, "Registro")
    categoria_label = CATEGORIA_FEEDBACK.get(categoria, categoria_label)
    slot.markdown(
        f'<div class="pc-feedback-top">'
        f'  <span class="pc-feedback-emoji">{html.escape(str(emoji))}</span>'
        f'  <span class="pc-feedback-text">'
        f'    <b>{html.escape(nome)}</b> registrado.'
        f'    <small>{html.escape(categoria_label)}</small>'
        f'  </span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _query_valor(nome: str) -> str:
    valor = st.query_params.get(nome)
    if isinstance(valor, list):
        return valor[0] if valor else ""
    return str(valor or "")


def _limpar_query_params() -> None:
    try:
        st.query_params.clear()
    except Exception:
        pass


def _limpar_url_cliente() -> None:
    components.html(
        """
        <script>
        (() => {
          try {
            const w = window.parent || window;
            if (w.location.search) {
              w.history.replaceState({}, "", w.location.pathname);
            }
          } catch (err) {}
        })();
        </script>
        """,
        height=1,
    )


def _instalar_feedback_cliente() -> None:
    components.html(
        """
        <script>
        (() => {
          const w = window.parent || window;
          if (w.__pictaFeedbackReady) return;
          w.__pictaFeedbackReady = true;
          w.__pictaShowPendingFeedback = (data = {}) => {
            try {
              const doc = w.document;
              let el = doc.getElementById("pc-client-feedback");
              if (!el) {
                el = doc.createElement("div");
                el.id = "pc-client-feedback";
                el.className = "pc-feedback-top pc-feedback-client";
                doc.body.appendChild(el);
              }

              el.textContent = "";

              const emoji = doc.createElement("span");
              emoji.className = "pc-feedback-emoji";
              emoji.textContent = data.emoji || "✓";

              const texto = doc.createElement("span");
              texto.className = "pc-feedback-text";

              const nome = doc.createElement("b");
              nome.textContent = data.nome || "Registrado";
              texto.appendChild(nome);
              texto.appendChild(doc.createTextNode(" registrado."));

              const categoria = doc.createElement("small");
              categoria.textContent = data.categoria || "Registro";
              texto.appendChild(categoria);

              el.appendChild(emoji);
              el.appendChild(texto);
              el.style.animation = "none";
              void el.offsetWidth;
              el.style.animation = "";

              const fallbackFala = [data.categoria, data.nome].filter(Boolean).join(": ");
              const falaTexto = data.fala || fallbackFala;
              const synth = w.speechSynthesis || window.speechSynthesis;
              if (falaTexto && synth) {
                const ultimo = w.__pictaLastSpoken || {};
                if (!(ultimo.texto === falaTexto && Date.now() - ultimo.ts < 5000)) {
                  synth.cancel();
                  const fala = new SpeechSynthesisUtterance(falaTexto);
                  fala.lang = "pt-BR";
                  fala.rate = 0.9;
                  fala.pitch = 1.05;
                  w.__pictaLastSpoken = { texto: falaTexto, ts: Date.now() };
                  synth.speak(fala);
                }
              }
            } catch (err) {}
          };

          w.document.addEventListener("click", (event) => {
            try {
              const alvo = event.target && event.target.closest
                ? event.target.closest("a.pc-picto-button[data-feedback]")
                : null;
              if (!alvo) return;
              w.__pictaShowPendingFeedback(JSON.parse(alvo.dataset.feedback || "{}"));
            } catch (err) {}
          }, true);
        })();
        </script>
        """,
        height=1,
    )


def _falar(texto: str) -> None:
    payload = json.dumps(texto, ensure_ascii=False)
    components.html(
        f"""
        <script>
        (() => {{
          const texto = {payload};
          try {{
            const w = window.parent || window;
            const ultimo = w.__pictaLastSpoken || {{}};
            if (ultimo.texto === texto && Date.now() - ultimo.ts < 5000) return;
            const synth = w.speechSynthesis || window.speechSynthesis;
            if (!synth) return;
            synth.cancel();
            const fala = new SpeechSynthesisUtterance(texto);
            fala.lang = 'pt-BR';
            fala.rate = 0.9;
            fala.pitch = 1.05;
            w.__pictaLastSpoken = {{ texto, ts: Date.now() }};
            synth.speak(fala);
          }} catch (err) {{
            console.warn('[PICTA] Voz indisponível:', err);
          }}
        }})();
        </script>
        """,
        height=1,
    )


def _instalar_fala_cliente() -> None:
    components.html(
        """
        <script>
        (() => {
          try {
            const w = window.parent || window;
            const doc = w.document;
            if (!doc || w.__pictaSpeakHandlerInstalled) return;
            w.__pictaSpeakHandlerInstalled = true;

            const limparTexto = (texto) => {
              const linhas = String(texto || "")
                .split(/\\n+/)
                .map((parte) => parte.trim())
                .filter(Boolean);
              const alvo = linhas.length > 1 ? linhas[linhas.length - 1] : linhas[0];
              return (alvo || "").replace(/^\\p{Extended_Pictographic}+/u, "").trim();
            };

            const falar = (texto) => {
              const synth = w.speechSynthesis || window.speechSynthesis;
              if (!synth || !texto || texto.toLowerCase() === "sair") return;
              synth.cancel();
              const fala = new SpeechSynthesisUtterance(texto);
              fala.lang = "pt-BR";
              fala.rate = 0.9;
              fala.pitch = 1.05;
              w.__pictaLastSpoken = { texto, ts: Date.now() };
              synth.speak(fala);
            };

            doc.addEventListener("click", (evento) => {
              const alvo = evento.target.closest("button, .pc-picto-button");
              if (!alvo) return;
              if (alvo.matches(".pc-picto-button")) return;
              const texto = limparTexto(alvo.innerText || alvo.textContent);
              if (texto && texto.toLowerCase() !== "sair") falar(texto);
            }, true);
          } catch (err) {
            console.warn("[PICTA] Nao foi possivel preparar a voz:", err);
          }
        })();
        </script>
        """,
        height=1,
    )


log_debug("painel_crianca.py carregado")
