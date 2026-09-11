"""Interface de coleta controlada para o estudo de campo do PICTA."""

from __future__ import annotations

import csv
import io
from datetime import datetime

import streamlit as st

from modules import pesquisa


def _duracao(inicio, fim) -> str:
    if not inicio or not fim:
        return "Em andamento"
    try:
        a = datetime.fromisoformat(str(inicio).replace("Z", "+00:00"))
        b = datetime.fromisoformat(str(fim).replace("Z", "+00:00"))
        return f"{max(0, int((b - a).total_seconds()))} s"
    except Exception:
        return "-"


def _baixar_csv(metricas: list[dict]) -> bytes:
    campos = [
        "codigo_participante",
        "faixa_etaria",
        "tarefa",
        "inicio",
        "fim",
        "duracao",
        "concluida",
        "solicitou_ajuda",
        "total_interacoes",
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=campos, extrasaction="ignore")
    writer.writeheader()
    for row in metricas:
        item = dict(row)
        item["duracao"] = _duracao(item.get("inicio"), item.get("fim"))
        writer.writerow(item)
    return buffer.getvalue().encode("utf-8-sig")


def _render_coleta(sessao_id: str) -> None:
    sessao = st.session_state.get("pesquisa_sessao") or {}
    tarefa = sessao.get("tarefa", "livre")
    titulo = pesquisa.TAREFAS.get(tarefa, "Exploração livre")

    st.markdown("## 🌟 Vamos conversar")
    st.markdown(f"### {titulo}")
    st.info("Toque em uma imagem para escolher. Você pode escolher mais de uma vez.")

    if "pesquisa_ajuda" not in st.session_state:
        st.session_state["pesquisa_ajuda"] = False
    if "pesquisa_ultima_escolha" not in st.session_state:
        st.session_state["pesquisa_ultima_escolha"] = ""

    categoria = None if tarefa == "livre" else tarefa
    pictos = pesquisa.obter_pictogramas_pesquisa(categoria)
    if not pictos:
        st.error("Nenhum pictograma disponível para esta tarefa.")
        return

    for inicio in range(0, len(pictos), 4):
        cols = st.columns(4)
        for col, picto in zip(cols, pictos[inicio : inicio + 4]):
            label = f"{picto.get('emoji') or '🔹'}\n{picto.get('nome', '')}"
            if col.button(label, key=f"pesq_picto_{sessao_id}_{picto['id']}", use_container_width=True):
                if pesquisa.registrar_interacao(sessao_id, int(picto["id"])):
                    st.session_state["pesquisa_ultima_escolha"] = str(picto.get("nome") or "")
                    st.rerun()

    if st.session_state.get("pesquisa_ultima_escolha"):
        st.success(f"Escolha registrada: {st.session_state['pesquisa_ultima_escolha']}")

    c1, c2 = st.columns(2)
    if c1.button("🙋 Precisei de ajuda", use_container_width=True):
        st.session_state["pesquisa_ajuda"] = True
        st.info("Ajuda marcada para esta sessão.")
    if c2.button("✅ Finalizar sessão", type="primary", use_container_width=True):
        ok = pesquisa.finalizar_sessao(
            sessao_id,
            concluida=True,
            solicitou_ajuda=bool(st.session_state.get("pesquisa_ajuda")),
        )
        if ok:
            st.session_state.pop("pesquisa_sessao", None)
            st.session_state.pop("pesquisa_ultima_escolha", None)
            st.session_state.pop("pesquisa_ajuda", None)
            st.success("Sessão finalizada e métricas salvas.")
            st.rerun()


def render() -> None:
    st.markdown("## 🧪 Coleta de pesquisa")
    st.caption(
        "Modo de coleta controlado para o TCC. Use somente após as autorizações "
        "éticas e institucionais aplicáveis ao estudo."
    )

    sessao = st.session_state.get("pesquisa_sessao")
    if sessao:
        _render_coleta(sessao["id"])
        return

    tab_coleta, tab_metricas = st.tabs(["Nova sessão", "Métricas"])

    with tab_coleta:
        participantes = pesquisa.listar_participantes()
        with st.expander("Cadastrar participante", expanded=not participantes):
            st.markdown("**Somente código e faixa etária. Não informe nome, CPF ou data de nascimento aqui.**")
            with st.form("pesquisa_novo_participante"):
                codigo = st.text_input("Código do participante", placeholder="P01")
                faixa = st.selectbox("Faixa etária", pesquisa.FAIXAS_ETARIAS)
                consentido = st.checkbox(
                    "Confirmo que o consentimento do responsável e o assentimento da criança foram obtidos conforme o protocolo aprovado.",
                    value=False,
                )
                if st.form_submit_button("Cadastrar participante", type="primary"):
                    ok, mensagem, participante_id = pesquisa.criar_participante(codigo, faixa, consentido)
                    if ok:
                        st.success(mensagem)
                        st.rerun()
                    else:
                        st.error(mensagem)

        participantes = pesquisa.listar_participantes()
        if not participantes:
            st.info("Cadastre o primeiro participante para iniciar uma sessão.")
            return

        opcoes = {f"{p['codigo_participante']} · {p['faixa_etaria']}": p["id"] for p in participantes}
        escolha = st.selectbox("Participante", list(opcoes))
        tarefa = st.selectbox(
            "Tarefa",
            list(pesquisa.TAREFAS),
            format_func=lambda chave: pesquisa.TAREFAS[chave],
        )
        if st.button("▶️ Iniciar sessão com a criança", type="primary", use_container_width=True):
            ok, mensagem, sessao_id = pesquisa.iniciar_sessao(opcoes[escolha], tarefa)
            if ok:
                st.session_state["pesquisa_sessao"] = {"id": sessao_id, "tarefa": tarefa}
                st.rerun()
            else:
                st.error(mensagem)

        st.warning(
            "Durante a sessão, não registre nome, endereço, diagnóstico, escola, imagem, áudio ou outras informações identificáveis em campos livres."
        )

    with tab_metricas:
        metricas = pesquisa.obter_metricas()
        if not metricas:
            st.info("Ainda não há sessões finalizadas para este pesquisador.")
        else:
            exibicao = []
            for row in metricas:
                item = dict(row)
                item["duracao"] = _duracao(item.get("inicio"), item.get("fim"))
                exibicao.append(item)
            st.dataframe(exibicao, use_container_width=True, hide_index=True)
            st.download_button(
                "⬇️ Baixar CSV pseudonimizado",
                data=_baixar_csv(metricas),
                file_name="picta_metricas_pesquisa.csv",
                mime="text/csv",
                use_container_width=True,
            )
