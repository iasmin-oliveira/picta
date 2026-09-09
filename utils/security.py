"""Security and object-level authorization for PICTA."""

from __future__ import annotations

from typing import Optional

from database.db import executar

ALLOWED_PROFILES = {"crianca", "responsavel", "cuidador", "profissional"}


def _current_user() -> Optional[dict]:
    try:
        import streamlit as st
        usuario = st.session_state.get("usuario") or {}
        if not st.session_state.get("autenticado") or not usuario.get("id"):
            return None
        return usuario
    except Exception:
        return None


def usuario_pode_acessar_crianca(usuario_id: int, perfil: str, crianca_id: int) -> bool:
    if not usuario_id or not crianca_id or perfil not in ALLOWED_PROFILES:
        return False
    row = executar("SELECT utilizador_id, cuidador_id FROM Criancas WHERE id = ?", (crianca_id,), fetchone=True)
    if not row:
        return False
    if perfil == "crianca":
        return int(row.get("utilizador_id") or 0) == int(usuario_id)
    if perfil in {"responsavel", "cuidador"}:
        return int(row.get("cuidador_id") or 0) == int(usuario_id)
    if perfil == "profissional":
        return bool(executar("SELECT id FROM Vinculos WHERE usuario_id = ? AND crianca_id = ?", (usuario_id, crianca_id), fetchone=True))
    return False


def exigir_acesso_crianca(crianca_id: int) -> bool:
    usuario = _current_user()
    if not usuario:
        return False
    return usuario_pode_acessar_crianca(int(usuario["id"]), str(usuario.get("perfil") or ""), int(crianca_id or 0))


def exigir_usuario_sessao(usuario_id: int) -> bool:
    """Ensure a sensitive account operation targets the authenticated user."""
    usuario = _current_user()
    if not usuario or not usuario_id:
        return False
    return int(usuario.get("id") or 0) == int(usuario_id)


def criar_ou_obter_crianca_do_usuario(usuario_id: int, nome: str) -> int:
    """Create/get only the child owned by this user. Never matches by name."""
    if not usuario_id:
        return 0
    row = executar("SELECT id FROM Criancas WHERE utilizador_id = ? ORDER BY id ASC LIMIT 1", (usuario_id,), fetchone=True)
    if row:
        return int(row["id"])
    nome_limpo = (nome or "Crianca").strip() or "Crianca"
    executar("INSERT INTO Criancas(nome, utilizador_id) VALUES(?,?)", (nome_limpo, usuario_id), commit=True)
    row = executar("SELECT id FROM Criancas WHERE utilizador_id = ? ORDER BY id ASC LIMIT 1", (usuario_id,), fetchone=True)
    return int(row["id"]) if row else 0


def obter_usuario_sessao() -> Optional[dict]:
    return _current_user()
