"""Camada de coleta de métricas para o estudo de campo do PICTA.

A coleta de pesquisa é separada dos cadastros clínicos existentes. O módulo
não exige nem grava nome, CPF, e-mail ou data de nascimento do participante.
A identificação do participante ocorre por código pseudônimo, e o acesso aos
registros fica vinculado ao profissional que os criou.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any, Optional

from database.db import executar, garantir_pictogramas_seed

ESTUDO_CODIGO = "PICTA-TCC-2026"
ESTUDO_NOME = "PICTA - estudo de usabilidade e comunicação"
FAIXAS_ETARIAS = ("7-8", "9-10")
TAREFAS = {
    "emocao": "Como estou me sentindo",
    "necessidade": "O que eu preciso",
    "acao": "O que eu quero fazer",
    "livre": "Exploração livre",
}
CODIGO_RE = re.compile(r"^P[0-9]{2,3}$", re.IGNORECASE)

_SCHEMA_READY = False


def _agora_sql() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat(sep=" ")


def _operador_atual() -> Optional[int]:
    try:
        import streamlit as st
    except Exception:
        return None
    if not st.session_state.get("autenticado"):
        return None
    usuario = st.session_state.get("usuario") or {}
    if str(usuario.get("perfil") or "") != "profissional":
        return None
    try:
        return int(usuario.get("id"))
    except (TypeError, ValueError):
        return None


def _garantir_schema() -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return

    ddl = (
        "CREATE TABLE IF NOT EXISTS Pesquisa_Estudos ("
        "id TEXT PRIMARY KEY, codigo TEXT UNIQUE NOT NULL, nome TEXT NOT NULL, "
        "ativo INTEGER DEFAULT 1, criado_em DATETIME DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS Pesquisa_Participantes ("
        "id TEXT PRIMARY KEY, estudo_id TEXT NOT NULL REFERENCES Pesquisa_Estudos(id) ON DELETE CASCADE, "
        "codigo_participante TEXT NOT NULL, faixa_etaria TEXT NOT NULL, "
        "consentimento_confirmado INTEGER NOT NULL DEFAULT 0, criado_por_usuario_id INTEGER NOT NULL REFERENCES Utilizadores(id), "
        "criado_em DATETIME DEFAULT CURRENT_TIMESTAMP, ativo INTEGER DEFAULT 1, "
        "UNIQUE(estudo_id, codigo_participante))",
        "CREATE TABLE IF NOT EXISTS Pesquisa_Sessoes ("
        "id TEXT PRIMARY KEY, participante_id TEXT NOT NULL REFERENCES Pesquisa_Participantes(id) ON DELETE CASCADE, "
        "operador_usuario_id INTEGER NOT NULL REFERENCES Utilizadores(id), tarefa TEXT NOT NULL, "
        "inicio DATETIME NOT NULL, fim DATETIME, concluida INTEGER DEFAULT 0, solicitou_ajuda INTEGER DEFAULT 0)",
        "CREATE TABLE IF NOT EXISTS Pesquisa_Interacoes ("
        "id TEXT PRIMARY KEY, sessao_id TEXT NOT NULL REFERENCES Pesquisa_Sessoes(id) ON DELETE CASCADE, "
        "pictograma_id INTEGER NOT NULL REFERENCES Pictogramas(id), ordem INTEGER NOT NULL, "
        "criado_em DATETIME DEFAULT CURRENT_TIMESTAMP)",
        "CREATE INDEX IF NOT EXISTS idx_pesquisa_participante_operador "
        "ON Pesquisa_Participantes(criado_por_usuario_id, ativo)",
        "CREATE INDEX IF NOT EXISTS idx_pesquisa_sessoes_participante "
        "ON Pesquisa_Sessoes(participante_id, inicio DESC)",
        "CREATE INDEX IF NOT EXISTS idx_pesquisa_interacoes_sessao "
        "ON Pesquisa_Interacoes(sessao_id, ordem)",
    )
    for statement in ddl:
        executar(statement, commit=True)

    estudo = executar(
        "SELECT id FROM Pesquisa_Estudos WHERE codigo = ?",
        (ESTUDO_CODIGO,),
        fetchone=True,
    )
    if not estudo:
        executar(
            "INSERT INTO Pesquisa_Estudos(id, codigo, nome) VALUES(?,?,?)",
            (uuid.uuid4().hex, ESTUDO_CODIGO, ESTUDO_NOME),
            commit=True,
        )
    _SCHEMA_READY = True


def _estudo_id() -> Optional[str]:
    row = executar(
        "SELECT id FROM Pesquisa_Estudos WHERE codigo = ? AND ativo = 1",
        (ESTUDO_CODIGO,),
        fetchone=True,
    )
    return row["id"] if row else None


def criar_participante(
    codigo: str,
    faixa_etaria: str,
    consentimento_confirmado: bool,
) -> tuple[bool, str, Optional[str]]:
    """Cria participante pseudônimo sem coletar identificadores diretos."""
    operador = _operador_atual()
    if not operador:
        return False, "Sessao de pesquisador invalida.", None
    codigo = str(codigo or "").strip().upper()
    if not CODIGO_RE.fullmatch(codigo):
        return False, "Use um código como P01, P02 ou P100.", None
    if faixa_etaria not in FAIXAS_ETARIAS:
        return False, "Faixa etaria invalida.", None
    if not consentimento_confirmado:
        return False, "Confirme que o consentimento do responsavel e o assentimento da crianca foram obtidos conforme o protocolo aprovado.", None

    _garantir_schema()
    estudo_id = _estudo_id()
    if not estudo_id:
        return False, "Estudo de pesquisa indisponivel.", None
    existente = executar(
        "SELECT id, criado_por_usuario_id FROM Pesquisa_Participantes "
        "WHERE estudo_id = ? AND codigo_participante = ? AND ativo = 1",
        (estudo_id, codigo),
        fetchone=True,
    )
    if existente:
        if int(existente["criado_por_usuario_id"]) != operador:
            return False, "Esse código de participante pertence a outro pesquisador.", None
        return True, "Participante ja cadastrado.", existente["id"]

    participante_id = uuid.uuid4().hex
    executar(
        "INSERT INTO Pesquisa_Participantes("
        "id, estudo_id, codigo_participante, faixa_etaria, consentimento_confirmado, criado_por_usuario_id) "
        "VALUES(?,?,?,?,?,?)",
        (participante_id, estudo_id, codigo, faixa_etaria, 1, operador),
        commit=True,
    )
    return True, "Participante cadastrado.", participante_id


def listar_participantes() -> list[dict[str, Any]]:
    operador = _operador_atual()
    if not operador:
        return []
    _garantir_schema()
    return executar(
        "SELECT id, codigo_participante, faixa_etaria, criado_em "
        "FROM Pesquisa_Participantes WHERE criado_por_usuario_id = ? AND ativo = 1 "
        "ORDER BY codigo_participante",
        (operador,),
        fetchall=True,
    ) or []


def iniciar_sessao(participante_id: str, tarefa: str) -> tuple[bool, str, Optional[str]]:
    operador = _operador_atual()
    if not operador:
        return False, "Sessao de pesquisador invalida.", None
    if tarefa not in TAREFAS:
        return False, "Tarefa de pesquisa invalida.", None
    _garantir_schema()
    participante = executar(
        "SELECT id FROM Pesquisa_Participantes "
        "WHERE id = ? AND criado_por_usuario_id = ? AND ativo = 1 AND consentimento_confirmado = 1",
        (participante_id, operador),
        fetchone=True,
    )
    if not participante:
        return False, "Participante nao autorizado para esta sessao.", None

    sessao_id = uuid.uuid4().hex
    executar(
        "INSERT INTO Pesquisa_Sessoes(id, participante_id, operador_usuario_id, tarefa, inicio) VALUES(?,?,?,?,?)",
        (sessao_id, participante_id, operador, tarefa, _agora_sql()),
        commit=True,
    )
    return True, "Sessao iniciada.", sessao_id


def registrar_interacao(sessao_id: str, pictograma_id: int) -> bool:
    operador = _operador_atual()
    if not operador or not sessao_id or not pictograma_id:
        return False
    _garantir_schema()
    sessao = executar(
        "SELECT id FROM Pesquisa_Sessoes WHERE id = ? AND operador_usuario_id = ? AND fim IS NULL",
        (sessao_id, operador),
        fetchone=True,
    )
    if not sessao:
        return False
    picto = executar(
        "SELECT id FROM Pictogramas WHERE id = ?",
        (pictograma_id,),
        fetchone=True,
    )
    if not picto:
        return False
    ordem = executar(
        "SELECT COUNT(*) AS total FROM Pesquisa_Interacoes WHERE sessao_id = ?",
        (sessao_id,),
        fetchone=True,
    )
    numero = int((ordem or {}).get("total") or 0) + 1
    executar(
        "INSERT INTO Pesquisa_Interacoes(id, sessao_id, pictograma_id, ordem) VALUES(?,?,?,?)",
        (uuid.uuid4().hex, sessao_id, pictograma_id, numero),
        commit=True,
    )
    return True


def finalizar_sessao(sessao_id: str, concluida: bool, solicitou_ajuda: bool) -> bool:
    operador = _operador_atual()
    if not operador or not sessao_id:
        return False
    _garantir_schema()
    sessao = executar(
        "SELECT id FROM Pesquisa_Sessoes WHERE id = ? AND operador_usuario_id = ? AND fim IS NULL",
        (sessao_id, operador),
        fetchone=True,
    )
    if not sessao:
        return False
    executar(
        "UPDATE Pesquisa_Sessoes SET fim = ?, concluida = ?, solicitou_ajuda = ? "
        "WHERE id = ? AND operador_usuario_id = ? AND fim IS NULL",
        (_agora_sql(), int(bool(concluida)), int(bool(solicitou_ajuda)), sessao_id, operador),
        commit=True,
    )
    return True


def obter_metricas() -> list[dict[str, Any]]:
    """Retorna somente métricas agregadas/pseudônimas do pesquisador atual."""
    operador = _operador_atual()
    if not operador:
        return []
    _garantir_schema()
    return executar(
        "SELECT p.codigo_participante, p.faixa_etaria, s.tarefa, s.inicio, s.fim, "
        "s.concluida, s.solicitou_ajuda, COUNT(i.id) AS total_interacoes "
        "FROM Pesquisa_Participantes p "
        "JOIN Pesquisa_Sessoes s ON s.participante_id = p.id "
        "LEFT JOIN Pesquisa_Interacoes i ON i.sessao_id = s.id "
        "WHERE p.criado_por_usuario_id = ? "
        "GROUP BY p.codigo_participante, p.faixa_etaria, s.tarefa, s.inicio, s.fim, s.concluida, s.solicitou_ajuda "
        "ORDER BY s.inicio DESC",
        (operador,),
        fetchall=True,
    ) or []


def obter_interacoes_sessao(sessao_id: str) -> list[dict[str, Any]]:
    operador = _operador_atual()
    if not operador:
        return []
    _garantir_schema()
    return executar(
        "SELECT i.ordem, p.nome AS pictograma, p.categoria, i.criado_em "
        "FROM Pesquisa_Interacoes i "
        "JOIN Pesquisa_Sessoes s ON s.id = i.sessao_id "
        "JOIN Pesquisa_Participantes pp ON pp.id = s.participante_id "
        "JOIN Pictogramas p ON p.id = i.pictograma_id "
        "WHERE i.sessao_id = ? AND s.operador_usuario_id = ? AND pp.criado_por_usuario_id = ? "
        "ORDER BY i.ordem",
        (sessao_id, operador, operador),
        fetchall=True,
    ) or []


def excluir_participante(participante_id: str) -> bool:
    """Exclui os dados pseudônimos do estudo para o pesquisador atual."""
    operador = _operador_atual()
    if not operador:
        return False
    _garantir_schema()
    participante = executar(
        "SELECT id FROM Pesquisa_Participantes WHERE id = ? AND criado_por_usuario_id = ?",
        (participante_id, operador),
        fetchone=True,
    )
    if not participante:
        return False
    executar(
        "DELETE FROM Pesquisa_Participantes WHERE id = ? AND criado_por_usuario_id = ?",
        (participante_id, operador),
        commit=True,
    )
    return True


def obter_pictogramas_pesquisa(categoria: Optional[str] = None) -> list[dict[str, Any]]:
    operador = _operador_atual()
    if not operador:
        return []
    garantir_pictogramas_seed()
    if categoria:
        return executar(
            "SELECT id, nome, categoria, emoji FROM Pictogramas WHERE categoria = ? ORDER BY id",
            (categoria,),
            fetchall=True,
        ) or []
    return executar(
        "SELECT id, nome, categoria, emoji FROM Pictogramas ORDER BY id",
        fetchall=True,
    ) or []
