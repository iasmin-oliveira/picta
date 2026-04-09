"""
PICTA — modules/logs.py
Registo e consulta de interações da criança com os pictogramas.
"""

from database.db import executar


def registar_interacao(crianca_id: int, pictograma_id: int) -> bool:
    try:
        executar(
            "INSERT INTO Registos_Interacao(crianca_id, pictograma_id) VALUES(?,?)",
            (crianca_id, pictograma_id),
            commit=True
        )
        return True
    except Exception as e:
        print(f"[PICTA] Erro ao registar interação: {e}")
        return False


def obter_interacoes(crianca_id: int) -> list[dict]:
    return executar(
        """SELECT ri.id, ri.registado_em,
                  p.nome AS pictograma, p.categoria, p.emoji
           FROM Registos_Interacao ri
           JOIN Pictogramas p ON p.id = ri.pictograma_id
           WHERE ri.crianca_id=?
           ORDER BY ri.registado_em DESC""",
        (crianca_id,),
        fetchall=True
    ) or []
