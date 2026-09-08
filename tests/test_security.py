import hashlib
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest


def make_db():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript("""
    CREATE TABLE Utilizadores (id INTEGER PRIMARY KEY, nome TEXT, perfil TEXT, username TEXT UNIQUE, email TEXT, senha_hash TEXT, deve_trocar_senha INTEGER DEFAULT 0);
    CREATE TABLE Criancas (id INTEGER PRIMARY KEY, nome TEXT, cuidador_id INTEGER, utilizador_id INTEGER, data_nascimento TEXT);
    CREATE TABLE Pictogramas (id INTEGER PRIMARY KEY, nome TEXT, categoria TEXT, emoji TEXT);
    CREATE TABLE Registos_Interacao (id INTEGER PRIMARY KEY, crianca_id INTEGER, pictograma_id INTEGER, registado_em TEXT);
    CREATE TABLE Vinculos (id INTEGER PRIMARY KEY, usuario_id INTEGER, crianca_id INTEGER);
    CREATE TABLE Sessoes (token TEXT PRIMARY KEY, usuario_id INTEGER, expira_em TEXT, ultima_atividade TEXT);
    """)
    return con


def test_password_hash_is_salted_and_verifies():
    from utils.passwords import hash_password, verify_password
    a, b = hash_password("senha-forte"), hash_password("senha-forte")
    assert a != b
    assert verify_password("senha-forte", a) == (True, False)
    assert verify_password("errada", a) == (False, False)


def test_legacy_sha256_migrates_on_login(monkeypatch):
    from modules import auth
    legacy = hashlib.sha256(b"senha123").hexdigest()
    rows = [{"id": 7, "nome": "Crianca A", "perfil": "crianca", "username": "a", "email": None, "senha_hash": legacy, "deve_trocar_senha": 0, "crianca_id": 10}]
    calls = []
    def fake_exec(sql, params=(), **kwargs):
        calls.append((sql, params, kwargs))
        if sql.startswith("SELECT u.id"):
            return dict(rows[0])
        return None
    monkeypatch.setattr(auth, "executar", fake_exec)
    user = auth.autenticar_usuario("A", "senha123")
    assert user["id"] == 7
    assert any("UPDATE Utilizadores SET senha_hash" in c[0] for c in calls)
    assert user.get("senha_hash") is None


def test_child_creation_never_reuses_same_name(monkeypatch):
    from modules import auth
    state = {"owned": None, "next": 20}
    def fake_exec(sql, params=(), **kwargs):
        if "SELECT id FROM Criancas WHERE utilizador_id" in sql:
            return state["owned"]
        if sql.startswith("INSERT INTO Criancas"):
            state["owned"] = {"id": state["next"]}
            state["next"] += 1
            return None
        return None
    monkeypatch.setattr(auth, "executar", fake_exec)
    first = auth.obter_ou_criar_crianca(1, "Ana")
    state["owned"] = None
    second = auth.obter_ou_criar_crianca(2, "Ana")
    assert first != second


def test_object_authorization_matrix(monkeypatch):
    from utils import security
    child = {"utilizador_id": 10, "cuidador_id": 20}
    def fake_exec(sql, params=(), **kwargs):
        if "SELECT utilizador_id" in sql:
            return child
        if "SELECT id FROM Vinculos" in sql:
            return {"id": 1} if params == (30, 99) else None
        return None
    monkeypatch.setattr(security, "executar", fake_exec)
    assert security.usuario_pode_acessar_crianca(10, "crianca", 99)
    assert not security.usuario_pode_acessar_crianca(11, "crianca", 99)
    assert security.usuario_pode_acessar_crianca(20, "cuidador", 99)
    assert not security.usuario_pode_acessar_crianca(21, "cuidador", 99)
    assert security.usuario_pode_acessar_crianca(30, "profissional", 99)
    assert not security.usuario_pode_acessar_crianca(31, "profissional", 99)


def test_unknown_profile_is_denied(monkeypatch):
    from utils import security
    monkeypatch.setattr(security, "executar", lambda *a, **k: {"utilizador_id": 1, "cuidador_id": 2})
    assert not security.usuario_pode_acessar_crianca(1, "admin", 9)


def test_session_expiration_and_revocation(monkeypatch):
    from modules import auth
    now = datetime.utcnow()
    row = {"id": 1, "nome": "A", "perfil": "crianca", "username": "a", "email": None, "deve_trocar_senha": 0, "crianca_id": 9, "ultima_atividade": (now - timedelta(minutes=31)).isoformat()}
    calls = []
    def fake_exec(sql, params=(), **kwargs):
        calls.append(sql)
        if sql.startswith("SELECT u.id"):
            return row
        return None
    monkeypatch.setattr(auth, "executar", fake_exec)
    assert auth.validar_sessao("token") is None
    assert any("DELETE FROM Sessoes" in s for s in calls)


def test_sql_is_parameterized_in_child_creation(monkeypatch):
    from modules import auth
    seen = []
    def fake_exec(sql, params=(), **kwargs):
        seen.append((sql, params))
        if "SELECT id FROM Criancas WHERE utilizador_id" in sql:
            return {"id": 1}
        return None
    monkeypatch.setattr(auth, "executar", fake_exec)
    auth.obter_ou_criar_crianca(1, "<script>alert(1)</script>")
    assert all("<script>" not in sql for sql, _ in seen)
    assert any(params == (1,) for _, params in seen)
