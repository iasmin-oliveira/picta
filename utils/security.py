"""Security and object-level authorization for PICTA.

All access to child records must pass through this module. The check is
performed against the authenticated Streamlit session and the database,
not against query-string values or UI selections.
"""

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


def usuario_pode_acessar_crianca(
    usuario_id: int,
    perfil: str,
    crianca_id: int,
) -> bool:
    """Return True only when the user has a database-backed relationship.

    Child accounts may access their own child record. Responsible/caregiver
    accounts may access children assigned to them. Professionals may access
    only children explicitly linked through Vinculos.
    """
    if not usuario_id or not crianca_id or perfil not in ALLOWED_PROFILES:
        return False

    row = executar(
        "SELECT utilizador_id, cuidador_id FROM Criancas WHERE id = ?",
        (crianca_id,),
        fetchone=True,
    )
    if not row:
        return False

    if perfil == "crianca":
        return int(row.get("utilizador_id") or 0) == int(usuario_id)

    if perfil in {"responsavel", "cuidador"}:
        return int(row.get("cuidador_id") or 0) == int(usuario_id)

    if perfil == "profissional":
        return bool(
            executar(
                "SELECT id FROM Vinculos WHERE usuario_id = ? AND crianca_id = ?",
                (usuario_id, crianca_id),
                fetchone=True,
            )
        )

    return False


def exigir_acesso_crianca(crianca_id: int) -> bool:
    """Enforce object-level authorization using the current authenticated session."""
    usuario = _current_user()
    if not usuario:
        return False
    return usuario_pode_acessar_crianca(
        int(usuario["id"]),
        str(usuario.get("perfil") or ""),
        int(crianca_id or 0),
    )


def obter_usuario_sessao() -> Optional[dict]:
    return _current_user()
