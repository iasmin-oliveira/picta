import os
import sys
import uuid

import pytest


def _fake_streamlit(monkeypatch, user_id, perfil="profissional"):
    session_state = {"autenticado": True, "usuario": {"id": user_id, "perfil": perfil}}
    fake_st = type("Streamlit", (), {"session_state": session_state})
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)
    return session_state


def _setup_sqlite(monkeypatch, tmp_path):
    from database import db
    monkeypatch.setattr(db, "SQLITE_PATH", tmp_path / "picta-research.db")
    monkeypatch.setattr(db, "_INITIALIZED", False)
    monkeypatch.setattr(db, "_PG_POOL", None)
    monkeypatch.setattr(db, "_usar_postgres", lambda: False)
    db.inicializar_db()
    return db


def _create_professional(db, username):
    from modules import auth
    assert auth.criar_usuario(
        username.title(), username, "senha123", "profissional", f"{username}@example.test"
    ) is None
    return db.executar(
        "SELECT id FROM Utilizadores WHERE username = ?", (username,), fetchone=True
    )["id"]


def test_research_collection_is_pseudonymous_and_requires_consent(monkeypatch, tmp_path):
    db = _setup_sqlite(monkeypatch, tmp_path)
    from modules import pesquisa

    pesquisa._SCHEMA_READY = False
    operator = _create_professional(db, "researcher_a")
    _fake_streamlit(monkeypatch, operator)

    ok, _, participant_id = pesquisa.criar_participante("P01", "7-8", False)
    assert not ok
    assert participant_id is None

    ok, _, participant_id = pesquisa.criar_participante("P01", "7-8", True)
    assert ok and participant_id

    columns = {
        row["name"]
        for row in db.executar(
            "SELECT name FROM pragma_table_info('Pesquisa_Participantes')", fetchall=True
        )
    }
    assert "nome" not in columns
    assert "data_nascimento" not in columns
    assert "cpf" not in columns
    assert "email" not in columns
    assert columns >= {
        "codigo_participante",
        "faixa_etaria",
        "consentimento_confirmado",
        "criado_por_usuario_id",
    }


def test_research_participant_and_session_isolation(monkeypatch, tmp_path):
    db = _setup_sqlite(monkeypatch, tmp_path)
    from modules import pesquisa

    pesquisa._SCHEMA_READY = False
    operator_a = _create_professional(db, "researcher_a")
    operator_b = _create_professional(db, "researcher_b")

    _fake_streamlit(monkeypatch, operator_a)
    ok, _, participant_a = pesquisa.criar_participante("P01", "7-8", True)
    assert ok
    ok, _, session_a = pesquisa.iniciar_sessao(participant_a, "emocao")
    assert ok and session_a
    picto = db.executar("SELECT id FROM Pictogramas LIMIT 1", fetchone=True)["id"]
    assert pesquisa.registrar_interacao(session_a, picto)

    _fake_streamlit(monkeypatch, operator_b)
    assert pesquisa.listar_participantes() == []
    assert pesquisa.registrar_interacao(session_a, picto) is False
    assert pesquisa.obter_interacoes_sessao(session_a) == []
    assert pesquisa.iniciar_sessao(participant_a, "emocao")[0] is False


def test_research_metrics_and_cascade_deletion(monkeypatch, tmp_path):
    db = _setup_sqlite(monkeypatch, tmp_path)
    from modules import pesquisa

    pesquisa._SCHEMA_READY = False
    operator = _create_professional(db, "researcher_a")
    _fake_streamlit(monkeypatch, operator)
    ok, _, participant_id = pesquisa.criar_participante("P02", "9-10", True)
    assert ok
    ok, _, session_id = pesquisa.iniciar_sessao(participant_id, "necessidade")
    assert ok
    picto = db.executar("SELECT id FROM Pictogramas LIMIT 1", fetchone=True)["id"]
    assert pesquisa.registrar_interacao(session_id, picto)
    assert pesquisa.finalizar_sessao(session_id, True, False)

    metrics = pesquisa.obter_metricas()
    assert len(metrics) == 1
    row = metrics[0]
    assert row["codigo_participante"] == "P02"
    assert row["faixa_etaria"] == "9-10"
    assert row["total_interacoes"] == 1
    assert "nome" not in row
    assert "data_nascimento" not in row

    assert pesquisa.excluir_participante(participant_id)
    assert db.executar(
        "SELECT COUNT(*) AS total FROM Pesquisa_Sessoes WHERE participante_id = ?",
        (participant_id,),
        fetchone=True,
    )["total"] == 0
    assert db.executar(
        "SELECT COUNT(*) AS total FROM Pesquisa_Interacoes WHERE sessao_id = ?",
        (session_id,),
        fetchone=True,
    )["total"] == 0


def test_research_code_and_task_validation(monkeypatch, tmp_path):
    db = _setup_sqlite(monkeypatch, tmp_path)
    from modules import pesquisa

    pesquisa._SCHEMA_READY = False
    operator = _create_professional(db, "researcher_a")
    _fake_streamlit(monkeypatch, operator)
    assert pesquisa.criar_participante("Maria", "7-8", True)[0] is False
    assert pesquisa.criar_participante("P01", "11-12", True)[0] is False
    ok, _, participant_id = pesquisa.criar_participante("P03", "7-8", True)
    assert ok
    assert pesquisa.iniciar_sessao(participant_id, "nao_existe")[0] is False


def test_research_postgres_isolation_and_schema(monkeypatch):
    if not os.getenv("DATABASE_URL"):
        pytest.skip("PostgreSQL de integração não configurado")

    from database import db
    from modules import auth, pesquisa

    db._INITIALIZED = False
    db._PG_POOL = None
    db.inicializar_db()
    pesquisa._SCHEMA_READY = False

    suffix = uuid.uuid4().hex[:10]
    user_a = f"research_a_{suffix}"
    user_b = f"research_b_{suffix}"
    assert auth.criar_usuario("Research A", user_a, "senha123", "profissional", f"{user_a}@example.test") is None
    assert auth.criar_usuario("Research B", user_b, "senha123", "profissional", f"{user_b}@example.test") is None
    id_a = db.executar("SELECT id FROM Utilizadores WHERE username = %s", (user_a,), fetchone=True)["id"]
    id_b = db.executar("SELECT id FROM Utilizadores WHERE username = %s", (user_b,), fetchone=True)["id"]

    _fake_streamlit(monkeypatch, id_a)
    ok, _, participant_id = pesquisa.criar_participante("P90", "9-10", True)
    assert ok
    ok, _, session_id = pesquisa.iniciar_sessao(participant_id, "acao")
    assert ok
    picto = db.executar("SELECT id FROM Pictogramas LIMIT 1", fetchone=True)["id"]
    assert pesquisa.registrar_interacao(session_id, picto)

    _fake_streamlit(monkeypatch, id_b)
    assert pesquisa.listar_participantes() == []
    assert pesquisa.registrar_interacao(session_id, picto) is False
    assert pesquisa.obter_metricas() == []
