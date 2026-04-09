"""
PICTA — modules/auth.py
Autenticação, sessões persistentes (cookie) e consultas de perfil.

Fluxo de login persistente:
  1. Utilizador faz login → gera token UUID → salva em Sessoes (BD) + cookie
  2. A cada carregamento da página → lê cookie → valida token no BD → restaura sessão
  3. Logout → apaga token do BD + apaga cookie
"""

import uuid
from datetime import datetime, timedelta

from database.db import executar, hash_senha


# ── Duração da sessão ────────────────────────────────────────────────────────
SESSION_DAYS = 7


def autenticar_usuario(username: str, senha: str) -> dict | None:
    """Valida credenciais. Retorna dict do utilizador ou None."""
    return executar(
        "SELECT id, nome, perfil, username FROM Utilizadores WHERE username=? AND senha_hash=?",
        (username.strip().lower(), hash_senha(senha)),
        fetchone=True
    )


def criar_sessao(usuario_id: int) -> str:
    """Cria token de sessão no BD e retorna o token (UUID)."""
    token = str(uuid.uuid4())
    expira = datetime.utcnow() + timedelta(days=SESSION_DAYS)
    # Remove sessões expiradas do mesmo utilizador
    executar(
        "DELETE FROM Sessoes WHERE usuario_id=? AND expira_em < ?",
        (usuario_id, datetime.utcnow().isoformat()),
        commit=True
    )
    executar(
        "INSERT INTO Sessoes(token, usuario_id, expira_em) VALUES(?,?,?)",
        (token, usuario_id, expira.isoformat()),
        commit=True
    )
    return token


def validar_sessao(token: str) -> dict | None:
    """
    Valida token de sessão. Retorna dict do utilizador se válido, None se expirado/inválido.
    """
    if not token:
        return None
    agora = datetime.utcnow().isoformat()
    row = executar(
        """SELECT u.id, u.nome, u.perfil, u.username
           FROM Sessoes s
           JOIN Utilizadores u ON u.id = s.usuario_id
           WHERE s.token=? AND s.expira_em > ?""",
        (token, agora),
        fetchone=True
    )
    return row


def revogar_sessao(token: str):
    """Remove o token do BD (logout)."""
    if token:
        executar("DELETE FROM Sessoes WHERE token=?", (token,), commit=True)


def obter_crianca_por_usuario_id(utilizador_id: int) -> dict | None:
    """Retorna os dados da Criança vinculados ao utilizador logado."""
    return executar(
        """SELECT c.id, c.nome, c.cuidador_id
           FROM Criancas c
           JOIN Utilizadores u ON u.nome = c.nome
           WHERE u.id=?""",
        (utilizador_id,),
        fetchone=True
    )


def obter_criancas_do_cuidador(cuidador_id: int) -> list[dict]:
    """Retorna todas as crianças vinculadas a um cuidador."""
    return executar(
        "SELECT id, nome, data_nascimento FROM Criancas WHERE cuidador_id=? ORDER BY nome",
        (cuidador_id,),
        fetchall=True
    ) or []
