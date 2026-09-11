"""Authentication, sessions, users and child/professional links."""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timedelta
from secrets import choice
from string import ascii_letters, digits
from typing import List, Optional

from database.db import executar
from modules.emailer import enviar_senha_temporaria, email_configurado
from utils.logger import get_logger
from utils.passwords import hash_password, verify_password

_log = get_logger(__name__)
INACTIVITY_MINUTES = 30
SESSION_MAX_HOURS = 8


def autenticar_usuario(username: str, senha: str) -> Optional[dict]:
    username = (username or "").strip().lower()
    if not username or not senha:
        return None
    result = executar(
        "SELECT u.id, u.nome, u.perfil, u.username, u.email, u.senha_hash, "
        "u.deve_trocar_senha, c.id AS crianca_id "
        "FROM Utilizadores u LEFT JOIN Criancas c ON c.utilizador_id = u.id "
        "WHERE u.username = ? ORDER BY c.id ASC LIMIT 1",
        (username,), fetchone=True,
    )
    if not result:
        _log.warning("Tentativa de login falhou: username=%s", username)
        return None
    valido, legado = verify_password(senha, result.get("senha_hash"))
    if not valido:
        _log.warning("Tentativa de login falhou: username=%s", username)
        return None
    if legado:
        executar("UPDATE Utilizadores SET senha_hash = ? WHERE id = ?", (hash_password(senha), result["id"]), commit=True)
        _log.info("Hash legado migrado para PBKDF2: usuario_id=%s", result["id"])
    result.pop("senha_hash", None)
    return result


def criar_usuario(nome: str, username: str, senha: str, perfil: str, email: str = "") -> Optional[str]:
    username, nome, email = username.strip().lower(), nome.strip(), email.strip().lower()
    if not nome or not username or not senha:
        return "Preencha todos os campos."
    if perfil in {"responsavel", "cuidador", "profissional"} and not email:
        return "Informe um email para recuperacao de senha."
    if email and "@" not in email:
        return "Informe um email valido."
    if len(senha) < 6:
        return "A senha deve ter pelo menos 6 caracteres."
    if perfil not in {"crianca", "responsavel", "cuidador", "profissional"}:
        return "Perfil invalido."
    if executar("SELECT id FROM Utilizadores WHERE username = ?", (username,), fetchone=True):
        return "Este nome de utilizador ja esta em uso."
    executar("INSERT INTO Utilizadores(nome, perfil, username, email, senha_hash) VALUES(?,?,?,?,?)", (nome, perfil, username, email or None, hash_password(senha)), commit=True)
    return None


def criar_sessao(usuario_id: int) -> str:
    token = uuid.uuid4().hex + uuid.uuid4().hex
    agora = datetime.utcnow()
    expira = agora + timedelta(hours=SESSION_MAX_HOURS)
    executar("INSERT INTO Sessoes(token, usuario_id, expira_em, ultima_atividade) VALUES(?,?,?,?)", (token, usuario_id, expira.isoformat(), agora.isoformat()), commit=True)
    _limpar_sessoes_expiradas_assincrono(usuario_id, agora)
    return token


def _limpar_sessoes_expiradas_assincrono(usuario_id: int, agora: datetime) -> None:
    def worker() -> None:
        try:
            executar("DELETE FROM Sessoes WHERE usuario_id = ? AND expira_em < ?", (usuario_id, agora.isoformat()), commit=True)
        except Exception as exc:
            _log.warning("Nao foi possivel limpar sessoes expiradas: %s", exc)
    threading.Thread(target=worker, name="picta-limpar-sessoes", daemon=True).start()


def validar_sessao(token: str) -> Optional[dict]:
    if not token:
        return None
    agora = datetime.utcnow()
    row = executar("SELECT u.id, u.nome, u.perfil, u.username, u.email, u.deve_trocar_senha, c.id AS crianca_id, s.ultima_atividade FROM Sessoes s JOIN Utilizadores u ON u.id = s.usuario_id LEFT JOIN Criancas c ON c.utilizador_id = u.id WHERE s.token = ? AND s.expira_em > ? ORDER BY c.id ASC LIMIT 1", (token, agora.isoformat()), fetchone=True)
    if not row:
        return None
    ultima = _parse_datetime(row.get("ultima_atividade"))
    if ultima and (agora - ultima.replace(tzinfo=None)).total_seconds() / 60 > INACTIVITY_MINUTES:
        revogar_sessao(token)
        return None
    return {k: v for k, v in row.items() if k != "ultima_atividade"}


def renovar_sessao(token: str) -> None:
    if token:
        executar("UPDATE Sessoes SET ultima_atividade = ? WHERE token = ?", (datetime.utcnow().isoformat(), token), commit=True)


def revogar_sessao(token: Optional[str]) -> None:
    if token:
        executar("DELETE FROM Sessoes WHERE token = ?", (token,), commit=True)


def obter_crianca_por_usuario_id(utilizador_id: int) -> Optional[dict]:
    if not utilizador_id:
        return None
    user = executar("SELECT nome FROM Utilizadores WHERE id = ?", (utilizador_id,), fetchone=True)
    if not user:
        return None
    crianca_id = obter_ou_criar_crianca(utilizador_id, user["nome"])
    return executar("SELECT id, nome, cuidador_id FROM Criancas WHERE id = ?", (crianca_id,), fetchone=True) if crianca_id else None


def obter_ou_criar_crianca(utilizador_id: int, nome: str) -> int:
    """Return only the record owned by the supplied child user. Never match by name."""
    if not utilizador_id:
        return 0
    row = executar("SELECT id FROM Criancas WHERE utilizador_id = ? ORDER BY id ASC LIMIT 1", (utilizador_id,), fetchone=True)
    if row:
        return int(row["id"])
    nome_limpo = (nome or "Crianca").strip() or "Crianca"
    try:
        executar("INSERT INTO Criancas(nome, utilizador_id) VALUES(?,?)", (nome_limpo, utilizador_id), commit=True)
    except Exception:
        row = executar("SELECT id FROM Criancas WHERE utilizador_id = ? ORDER BY id ASC LIMIT 1", (utilizador_id,), fetchone=True)
        return int(row["id"]) if row else 0
    row = executar("SELECT id FROM Criancas WHERE utilizador_id = ? ORDER BY id ASC LIMIT 1", (utilizador_id,), fetchone=True)
    return int(row["id"]) if row else 0


def criar_crianca_para_utilizador(utilizador_id: int, nome: str) -> int:
    return obter_ou_criar_crianca(utilizador_id, nome)


def obter_criancas_do_usuario(usuario_id: int, perfil: str) -> List[dict]:
    from utils.security import exigir_usuario_sessao
    if not usuario_id or not exigir_usuario_sessao(usuario_id):
        return []
    perfil_db = executar("SELECT perfil FROM Utilizadores WHERE id = ?", (usuario_id,), fetchone=True)
    perfil_real = str((perfil_db or {}).get("perfil") or "")
    if perfil_real != perfil:
        return []
    if perfil_real in ("responsavel", "cuidador"):
        return executar("SELECT id, nome, data_nascimento FROM Criancas WHERE cuidador_id = ? ORDER BY nome", (usuario_id,), fetchall=True) or []
    if perfil_real == "profissional":
        return executar("SELECT c.id, c.nome, c.data_nascimento FROM Criancas c JOIN Vinculos v ON v.crianca_id = c.id WHERE v.usuario_id = ? ORDER BY c.nome", (usuario_id,), fetchall=True) or []
    return []


def vincular_crianca_responsavel(responsavel_id: int, crianca_username: str) -> Optional[str]:
    from utils.security import exigir_usuario_sessao
    if not responsavel_id or not exigir_usuario_sessao(responsavel_id):
        return "Sessao invalida. Faca login novamente."
    resp = executar("SELECT perfil FROM Utilizadores WHERE id = ?", (responsavel_id,), fetchone=True)
    if str((resp or {}).get("perfil") or "") not in {"responsavel", "cuidador"}:
        return "Perfil sem permissao para vincular criancas."
    crianca_user = executar("SELECT id, nome, perfil FROM Utilizadores WHERE username = ?", (crianca_username.strip().lower(),), fetchone=True)
    if not crianca_user:
        return "Utilizador nao encontrado."
    if crianca_user["perfil"] != "crianca":
        return "Este utilizador nao tem o perfil Crianca."
    crianca_id = obter_ou_criar_crianca(crianca_user["id"], crianca_user["nome"])
    if not crianca_id:
        return "Nao foi possivel preparar o registro da crianca."
    executar("UPDATE Criancas SET cuidador_id = ? WHERE id = ?", (responsavel_id, crianca_id), commit=True)
    return None


def convidar_profissional(responsavel_id: int, prof_username: str, crianca_id: int) -> Optional[str]:
    from utils.security import exigir_usuario_sessao
    if not responsavel_id or not exigir_usuario_sessao(responsavel_id):
        return "Sessao invalida. Faca login novamente."
    if not executar("SELECT id FROM Criancas WHERE id = ? AND cuidador_id = ?", (crianca_id, responsavel_id), fetchone=True):
        return "Crianca nao encontrada ou sem permissao."
    prof = executar("SELECT id, perfil FROM Utilizadores WHERE username = ?", (prof_username.strip().lower(),), fetchone=True)
    if not prof:
        return "Profissional nao encontrado."
    if prof["perfil"] != "profissional":
        return "Este utilizador nao tem o perfil Profissional de Saude."
    if executar("SELECT id FROM Vinculos WHERE usuario_id = ? AND crianca_id = ?", (prof["id"], crianca_id), fetchone=True):
        return "Este profissional ja tem acesso a esta crianca."
    executar("INSERT INTO Vinculos(usuario_id, crianca_id) VALUES(?,?)", (prof["id"], crianca_id), commit=True)
    return None


def obter_usuario_por_id(usuario_id: int) -> Optional[dict]:
    from utils.security import exigir_usuario_sessao
    if not usuario_id or not exigir_usuario_sessao(usuario_id):
        return None
    return executar("SELECT id, nome, username, email, perfil FROM Utilizadores WHERE id = ?", (usuario_id,), fetchone=True)


def atualizar_usuario(usuario_id: int, nome: str, username: str, nova_senha: str = "", email: Optional[str] = None) -> Optional[str]:
    from utils.security import exigir_usuario_sessao
    if not usuario_id or not exigir_usuario_sessao(usuario_id):
        return "Sessao invalida. Faca login novamente."
    nome, username = nome.strip(), username.strip().lower()
    email_limpo = email.strip().lower() if email is not None else None
    if not nome or not username:
        return "Nome e nome de utilizador sao obrigatorios."
    if email_limpo is not None and email_limpo and "@" not in email_limpo:
        return "Informe um email valido."
    if executar("SELECT id FROM Utilizadores WHERE username = ? AND id != ?", (username, usuario_id), fetchone=True):
        return "Este nome de utilizador ja esta em uso por outra conta."
    campos, params = ["nome = ?", "username = ?"], [nome, username]
    if email_limpo is not None:
        campos.append("email = ?")
        params.append(email_limpo or None)
    if nova_senha:
        if len(nova_senha) < 6:
            return "A nova senha deve ter pelo menos 6 caracteres."
        campos.extend(["senha_hash = ?", "deve_trocar_senha = ?"])
        params.extend([hash_password(nova_senha), False])
    params.append(usuario_id)
    executar(f"UPDATE Utilizadores SET {', '.join(campos)} WHERE id = ?", tuple(params), commit=True)
    return None


def solicitar_recuperacao_senha(email: str) -> Optional[str]:
    email = email.strip().lower()
    if not email or "@" not in email:
        return "Informe um email valido."
    if not email_configurado():
        return "Envio de email ainda nao configurado para este ambiente."
    usuarios = executar("SELECT id, nome, email FROM Utilizadores WHERE LOWER(TRIM(email)) = LOWER(TRIM(?)) AND perfil IN ('responsavel', 'cuidador', 'profissional') LIMIT 2", (email,), fetchall=True) or []
    if len(usuarios) != 1:
        return None
    usuario = usuarios[0]
    senha_temporaria = _gerar_senha_temporaria()
    erro_envio = enviar_senha_temporaria(usuario["email"], usuario["nome"], senha_temporaria)
    if erro_envio:
        return erro_envio
    executar("UPDATE Utilizadores SET senha_hash = ?, deve_trocar_senha = ? WHERE id = ?", (hash_password(senha_temporaria), True, usuario["id"]), commit=True)
    return None


def trocar_senha_obrigatoria(usuario_id: int, nova_senha: str) -> Optional[str]:
    from utils.security import exigir_usuario_sessao
    if not usuario_id or not exigir_usuario_sessao(usuario_id):
        return "Sessao invalida. Faca login novamente."
    if len(nova_senha or "") < 6:
        return "A nova senha deve ter pelo menos 6 caracteres."
    executar("UPDATE Utilizadores SET senha_hash = ?, deve_trocar_senha = ? WHERE id = ?", (hash_password(nova_senha), False, usuario_id), commit=True)
    return None


def atualizar_senha_crianca_responsavel(responsavel_id: int, crianca_id: int, nova_senha: str) -> Optional[str]:
    from utils.security import exigir_usuario_sessao
    if not responsavel_id or not exigir_usuario_sessao(responsavel_id):
        return "Sessao invalida. Faca login novamente."
    if len(nova_senha or "") < 6:
        return "A nova senha deve ter pelo menos 6 caracteres."
    row = executar("SELECT utilizador_id FROM Criancas WHERE id = ? AND cuidador_id = ?", (crianca_id, responsavel_id), fetchone=True)
    if not row or not row.get("utilizador_id"):
        return "Crianca nao encontrada ou sem conta vinculada."
    executar("UPDATE Utilizadores SET senha_hash = ?, deve_trocar_senha = ? WHERE id = ?", (hash_password(nova_senha), False, row["utilizador_id"]), commit=True)
    return None


def _gerar_senha_temporaria(tamanho: int = 10) -> str:
    alfabeto = ascii_letters + digits
    return "".join(choice(alfabeto) for _ in range(tamanho))


def atualizar_crianca(crianca_id: int, nome: str, data_nascimento: str = "", usuario_id: Optional[int] = None, perfil: Optional[str] = None) -> Optional[str]:
    nome = nome.strip()
    if not crianca_id:
        return "Crianca invalida."
    if not nome:
        return "O nome da crianca e obrigatorio."
    if usuario_id is None or perfil is None:
        return "Sessao/permissao nao informada."
    from utils.security import usuario_pode_acessar_crianca
    if not usuario_pode_acessar_crianca(usuario_id, perfil, crianca_id):
        return "Crianca nao encontrada ou sem permissao."
    executar("UPDATE Criancas SET nome = ?, data_nascimento = ? WHERE id = ?", (nome, data_nascimento or None, crianca_id), commit=True)
    return None


def obter_crianca_por_id(crianca_id: int, usuario_id: Optional[int] = None, perfil: Optional[str] = None) -> Optional[dict]:
    if not crianca_id or usuario_id is None or perfil is None:
        return None
    from utils.security import usuario_pode_acessar_crianca
    if not usuario_pode_acessar_crianca(usuario_id, perfil, crianca_id):
        return None
    return executar("SELECT id, nome, data_nascimento, cuidador_id, utilizador_id FROM Criancas WHERE id = ?", (crianca_id,), fetchone=True)


def listar_profissionais_da_crianca(crianca_id: int) -> List[dict]:
    from utils.security import exigir_acesso_crianca
    if not exigir_acesso_crianca(crianca_id):
        return []
    return executar("SELECT u.id, u.nome, u.username FROM Utilizadores u JOIN Vinculos v ON v.usuario_id = u.id WHERE v.crianca_id = ? ORDER BY u.nome", (crianca_id,), fetchall=True) or []


def _parse_datetime(value) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
