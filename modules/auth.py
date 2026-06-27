"""Authentication, sessions, users and child/professional links."""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from database.db import executar, hash_senha
from utils.logger import get_logger

_log = get_logger(__name__)

INACTIVITY_MINUTES = 30


def autenticar_usuario(username: str, senha: str) -> Optional[dict]:
    username = username.strip().lower()
    if not username or not senha:
        return None

    result = executar(
        "SELECT id, nome, perfil, username FROM Utilizadores "
        "WHERE username = ? AND senha_hash = ?",
        (username, hash_senha(senha)),
        fetchone=True,
    )
    if result:
        _log.info("Login bem-sucedido: username=%s perfil=%s", username, result.get("perfil"))
    else:
        _log.warning("Tentativa de login falhou: username=%s", username)
    return result


def criar_usuario(nome: str, username: str, senha: str, perfil: str) -> Optional[str]:
    username = username.strip().lower()
    nome = nome.strip()
    if not nome or not username or not senha:
        return "Preencha todos os campos."
    if len(senha) < 6:
        return "A senha deve ter pelo menos 6 caracteres."
    if perfil not in {"crianca", "responsavel", "cuidador", "profissional"}:
        return "Perfil invalido."
    if executar("SELECT id FROM Utilizadores WHERE username = ?", (username,), fetchone=True):
        _log.warning("Tentativa de cadastro com username duplicado: %s", username)
        return "Este nome de utilizador ja esta em uso."

    executar(
        "INSERT INTO Utilizadores(nome, perfil, username, senha_hash) VALUES(?,?,?,?)",
        (nome, perfil, username, hash_senha(senha)),
        commit=True,
    )
    _log.info("Novo utilizador criado: username=%s perfil=%s", username, perfil)
    return None


def criar_sessao(usuario_id: int) -> str:
    token = str(uuid.uuid4())
    agora = datetime.utcnow()
    expira = agora + timedelta(days=30)
    executar(
        "INSERT INTO Sessoes(token, usuario_id, expira_em, ultima_atividade) VALUES(?,?,?,?)",
        (token, usuario_id, expira.isoformat(), agora.isoformat()),
        commit=True,
    )
    _limpar_sessoes_expiradas_assincrono(usuario_id, agora)
    _log.info("Sessao criada: usuario_id=%s", usuario_id)
    return token


def _limpar_sessoes_expiradas_assincrono(usuario_id: int, agora: datetime) -> None:
    def worker() -> None:
        try:
            executar(
                "DELETE FROM Sessoes WHERE usuario_id = ? AND expira_em < ?",
                (usuario_id, agora.isoformat()),
                commit=True,
            )
        except Exception as exc:
            _log.warning("Nao foi possivel limpar sessoes expiradas: %s", exc)

    threading.Thread(target=worker, name="picta-limpar-sessoes", daemon=True).start()


def validar_sessao(token: str) -> Optional[dict]:
    if not token:
        return None

    agora = datetime.utcnow()
    row = executar(
        "SELECT u.id, u.nome, u.perfil, u.username, s.ultima_atividade "
        "FROM Sessoes s JOIN Utilizadores u ON u.id = s.usuario_id "
        "WHERE s.token = ? AND s.expira_em > ?",
        (token, agora.isoformat()),
        fetchone=True,
    )
    if not row:
        return None

    ultima = _parse_datetime(row.get("ultima_atividade"))
    if ultima:
        minutos = (agora - ultima.replace(tzinfo=None)).total_seconds() / 60
        if minutos > INACTIVITY_MINUTES:
            _log.info("Sessao expirada por inatividade: usuario_id=%s", row.get("id"))
            revogar_sessao(token)
            return None

    return {k: v for k, v in row.items() if k != "ultima_atividade"}


def renovar_sessao(token: str) -> None:
    if token:
        executar(
            "UPDATE Sessoes SET ultima_atividade = ? WHERE token = ?",
            (datetime.utcnow().isoformat(), token),
            commit=True,
        )


def revogar_sessao(token: Optional[str]) -> None:
    if token:
        executar("DELETE FROM Sessoes WHERE token = ?", (token,), commit=True)
        _log.info("Sessao revogada.")


def obter_crianca_por_usuario_id(utilizador_id: int) -> Optional[dict]:
    if not utilizador_id:
        return None

    user = executar(
        "SELECT nome FROM Utilizadores WHERE id = ?",
        (utilizador_id,),
        fetchone=True,
    )
    if not user:
        return None

    crianca_id = obter_ou_criar_crianca(utilizador_id, user["nome"])
    if not crianca_id:
        return None

    return executar(
        "SELECT id, nome, cuidador_id FROM Criancas WHERE id = ?",
        (crianca_id,),
        fetchone=True,
    )


def obter_ou_criar_crianca(utilizador_id: int, nome: str) -> int:
    if not utilizador_id:
        return 0

    nome_limpo = (nome or "Crianca").strip()
    por_usuario = executar(
        "SELECT id, nome, cuidador_id FROM Criancas WHERE utilizador_id = ? "
        "ORDER BY id ASC LIMIT 1",
        (utilizador_id,),
        fetchone=True,
    )
    por_nome = _buscar_crianca_canonica_por_nome(nome_limpo)

    if por_usuario and por_nome and int(por_usuario["id"]) != int(por_nome["id"]):
        return _mesclar_criancas(
            origem_id=int(por_usuario["id"]),
            destino_id=int(por_nome["id"]),
            utilizador_id=utilizador_id,
            nome=nome_limpo,
        )

    if por_usuario:
        return int(por_usuario["id"])

    if por_nome:
        executar(
            "UPDATE Criancas SET utilizador_id = ? WHERE id = ?",
            (utilizador_id, por_nome["id"]),
            commit=True,
        )
        return int(por_nome["id"])

    executar(
        "INSERT INTO Criancas(nome, utilizador_id) VALUES(?,?)",
        (nome_limpo, utilizador_id),
        commit=True,
    )
    row = executar(
        "SELECT id FROM Criancas WHERE utilizador_id = ? ORDER BY id ASC LIMIT 1",
        (utilizador_id,),
        fetchone=True,
    )
    return int(row["id"]) if row else 0


def _buscar_crianca_canonica_por_nome(nome: str) -> Optional[dict]:
    return executar(
        "SELECT id, nome, cuidador_id FROM Criancas "
        "WHERE LOWER(TRIM(nome)) = LOWER(TRIM(?)) "
        "ORDER BY CASE WHEN cuidador_id IS NOT NULL THEN 0 ELSE 1 END, id ASC "
        "LIMIT 1",
        (nome,),
        fetchone=True,
    )


def _mesclar_criancas(
    origem_id: int,
    destino_id: int,
    utilizador_id: int,
    nome: str,
) -> int:
    if origem_id == destino_id:
        return destino_id

    origem = executar(
        "SELECT cuidador_id FROM Criancas WHERE id = ?",
        (origem_id,),
        fetchone=True,
    )
    destino = executar(
        "SELECT cuidador_id FROM Criancas WHERE id = ?",
        (destino_id,),
        fetchone=True,
    )
    cuidador_id = (destino or {}).get("cuidador_id") or (origem or {}).get("cuidador_id")

    executar(
        "UPDATE Registos_Interacao SET crianca_id = ? WHERE crianca_id = ?",
        (destino_id, origem_id),
        commit=True,
    )

    vinculos = executar(
        "SELECT usuario_id FROM Vinculos WHERE crianca_id = ?",
        (origem_id,),
        fetchall=True,
    ) or []
    for vinculo in vinculos:
        if not executar(
            "SELECT id FROM Vinculos WHERE usuario_id = ? AND crianca_id = ?",
            (vinculo["usuario_id"], destino_id),
            fetchone=True,
        ):
            executar(
                "INSERT INTO Vinculos(usuario_id, crianca_id) VALUES(?,?)",
                (vinculo["usuario_id"], destino_id),
                commit=True,
            )
    executar("DELETE FROM Vinculos WHERE crianca_id = ?", (origem_id,), commit=True)

    executar(
        "UPDATE Criancas SET utilizador_id = NULL WHERE id = ?",
        (origem_id,),
        commit=True,
    )
    executar(
        "UPDATE Criancas SET nome = ?, cuidador_id = ?, utilizador_id = ? WHERE id = ?",
        (nome, cuidador_id, utilizador_id, destino_id),
        commit=True,
    )
    executar("DELETE FROM Criancas WHERE id = ?", (origem_id,), commit=True)

    return destino_id


def criar_crianca_para_utilizador(utilizador_id: int, nome: str) -> int:
    return obter_ou_criar_crianca(utilizador_id, nome)


def obter_criancas_do_usuario(usuario_id: int, perfil: str) -> List[dict]:
    if not usuario_id:
        return []

    if perfil in ("responsavel", "cuidador"):
        return executar(
            "SELECT id, nome, data_nascimento FROM Criancas "
            "WHERE cuidador_id = ? ORDER BY nome",
            (usuario_id,),
            fetchall=True,
        ) or []

    if perfil == "profissional":
        return executar(
            "SELECT c.id, c.nome, c.data_nascimento FROM Criancas c "
            "JOIN Vinculos v ON v.crianca_id = c.id "
            "WHERE v.usuario_id = ? ORDER BY c.nome",
            (usuario_id,),
            fetchall=True,
        ) or []

    return []


def vincular_crianca_responsavel(responsavel_id: int, crianca_username: str) -> Optional[str]:
    if not responsavel_id:
        return "Sessao invalida. Faca login novamente."

    crianca_user = executar(
        "SELECT id, nome, perfil FROM Utilizadores WHERE username = ?",
        (crianca_username.strip().lower(),),
        fetchone=True,
    )
    if not crianca_user:
        return "Utilizador nao encontrado."
    if crianca_user["perfil"] != "crianca":
        return "Este utilizador nao tem o perfil Crianca."

    crianca_id = obter_ou_criar_crianca(crianca_user["id"], crianca_user["nome"])
    if not crianca_id:
        return "Nao foi possivel preparar o registro da crianca."

    executar(
        "UPDATE Criancas SET cuidador_id = ? WHERE id = ?",
        (responsavel_id, crianca_id),
        commit=True,
    )
    return None


def convidar_profissional(
    responsavel_id: int,
    prof_username: str,
    crianca_id: int,
) -> Optional[str]:
    if not responsavel_id:
        return "Sessao invalida. Faca login novamente."

    if not executar(
        "SELECT id FROM Criancas WHERE id = ? AND cuidador_id = ?",
        (crianca_id, responsavel_id),
        fetchone=True,
    ):
        return "Crianca nao encontrada ou sem permissao."

    prof = executar(
        "SELECT id, perfil FROM Utilizadores WHERE username = ?",
        (prof_username.strip().lower(),),
        fetchone=True,
    )
    if not prof:
        return "Profissional nao encontrado."
    if prof["perfil"] != "profissional":
        return "Este utilizador nao tem o perfil Profissional de Saude."

    if executar(
        "SELECT id FROM Vinculos WHERE usuario_id = ? AND crianca_id = ?",
        (prof["id"], crianca_id),
        fetchone=True,
    ):
        return "Este profissional ja tem acesso a esta crianca."

    executar(
        "INSERT INTO Vinculos(usuario_id, crianca_id) VALUES(?,?)",
        (prof["id"], crianca_id),
        commit=True,
    )
    return None


def obter_usuario_por_id(usuario_id: int) -> Optional[dict]:
    if not usuario_id:
        return None
    return executar(
        "SELECT id, nome, username, perfil FROM Utilizadores WHERE id = ?",
        (usuario_id,),
        fetchone=True,
    )


def atualizar_usuario(
    usuario_id: int,
    nome: str,
    username: str,
    nova_senha: str = "",
) -> Optional[str]:
    if not usuario_id:
        return "Sessao invalida. Faca login novamente."

    nome = nome.strip()
    username = username.strip().lower()
    if not nome or not username:
        return "Nome e nome de utilizador sao obrigatorios."

    existe = executar(
        "SELECT id FROM Utilizadores WHERE username = ? AND id != ?",
        (username, usuario_id),
        fetchone=True,
    )
    if existe:
        return "Este nome de utilizador ja esta em uso por outra conta."

    if nova_senha:
        if len(nova_senha) < 6:
            return "A nova senha deve ter pelo menos 6 caracteres."
        executar(
            "UPDATE Utilizadores SET nome = ?, username = ?, senha_hash = ? WHERE id = ?",
            (nome, username, hash_senha(nova_senha), usuario_id),
            commit=True,
        )
    else:
        executar(
            "UPDATE Utilizadores SET nome = ?, username = ? WHERE id = ?",
            (nome, username, usuario_id),
            commit=True,
        )
    return None


def atualizar_crianca(crianca_id: int, nome: str, data_nascimento: str = "") -> Optional[str]:
    nome = nome.strip()
    if not crianca_id:
        return "Crianca invalida."
    if not nome:
        return "O nome da crianca e obrigatorio."
    executar(
        "UPDATE Criancas SET nome = ?, data_nascimento = ? WHERE id = ?",
        (nome, data_nascimento or None, crianca_id),
        commit=True,
    )
    return None


def obter_crianca_por_id(crianca_id: int) -> Optional[dict]:
    if not crianca_id:
        return None
    return executar(
        "SELECT id, nome, data_nascimento FROM Criancas WHERE id = ?",
        (crianca_id,),
        fetchone=True,
    )


def listar_profissionais_da_crianca(crianca_id: int) -> List[dict]:
    if not crianca_id:
        return []
    return executar(
        "SELECT u.id, u.nome, u.username FROM Vinculos v "
        "JOIN Utilizadores u ON u.id = v.usuario_id "
        "WHERE v.crianca_id = ? ORDER BY u.nome",
        (crianca_id,),
        fetchall=True,
    ) or []


def _parse_datetime(value) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
