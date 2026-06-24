"""Registro e consulta das interações da criança com os pictogramas."""

from __future__ import annotations

import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

from database.db import executar
from utils.debug_logger import log_debug

APP_TZ = ZoneInfo("America/Sao_Paulo")


def registar_interacao(crianca_id: int, pictograma_id: int) -> bool:
    if not crianca_id or not pictograma_id:
        return False
    try:
        executar(
            "INSERT INTO Registos_Interacao(crianca_id, pictograma_id) VALUES(?,?)",
            (crianca_id, pictograma_id),
            commit=True,
        )
        return True
    except Exception as exc:
        print("[PICTA] Erro ao registrar interação:", exc)
        return False


def obter_interacoes(crianca_id: int, limite: int = 200) -> List[dict]:
    if not crianca_id:
        return []
    rows = executar(
        "SELECT ri.id, ri.registado_em, "
        "p.nome AS pictograma, p.categoria, p.emoji "
        "FROM Registos_Interacao ri "
        "JOIN Pictogramas p ON p.id = ri.pictograma_id "
        "WHERE ri.crianca_id = ? "
        "ORDER BY ri.registado_em DESC "
        "LIMIT ?",
        (crianca_id, limite),
        fetchall=True,
    ) or []
    return _normalizar_registos(rows)


def obter_interacoes_periodo(
    crianca_id: int,
    data_inicio: Optional[datetime.date] = None,
    data_fim: Optional[datetime.date] = None,
) -> List[dict]:
    if not crianca_id:
        return []

    query = (
        "SELECT ri.id, ri.registado_em, ri.crianca_id, ri.pictograma_id, "
        "p.nome AS pictograma, p.categoria, p.emoji "
        "FROM Registos_Interacao ri "
        "JOIN Pictogramas p ON p.id = ri.pictograma_id "
        "WHERE ri.crianca_id = ?"
    )
    params: list = [crianca_id]

    if data_inicio:
        query += " AND ri.registado_em >= ?"
        params.append(_inicio_local_para_utc(data_inicio))
    if data_fim:
        query += " AND ri.registado_em < ?"
        params.append(_inicio_local_para_utc(data_fim + datetime.timedelta(days=1)))

    query += " ORDER BY ri.registado_em ASC"
    rows = executar(query, tuple(params), fetchall=True) or []
    return _normalizar_registos(rows)


def _normalizar_registos(rows: List[dict]) -> List[dict]:
    for row in rows:
        row["registado_em_utc"] = row.get("registado_em")
        row["registado_em"] = _para_data_hora_local(row.get("registado_em"))
    return rows


def _para_data_hora_local(value) -> str:
    if not value:
        return ""
    if isinstance(value, datetime.datetime):
        dt = value
    else:
        dt = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(APP_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _inicio_local_para_utc(data: datetime.date) -> str:
    inicio_local = datetime.datetime.combine(data, datetime.time.min, tzinfo=APP_TZ)
    return inicio_local.astimezone(datetime.timezone.utc).replace(tzinfo=None).isoformat()


log_debug("modules/logs.py carregado")
