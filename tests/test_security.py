import hashlib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


def test_password_hash_is_salted_and_verifies():
    from utils.passwords import hash_password, verify_password
    a, b = hash_password("senha-forte"), hash_password("senha-forte")
    assert a != b
    assert verify_password("senha-forte", a) == (True, False)
    assert verify_password("errada", a) == (False, False)


def test_legacy_sha256_migrates_on_login(monkeypatch):
    from modules import auth
    legacy = hashlib.sha256(b"senha123").hexdigest()
    row = {"id": 7, "nome": "Crianca A", "perfil": "crianca", "username": "a", "email": None, "senha_hash": legacy, "deve_trocar_senha": 0, "crianca_id": 10}
    calls = []
    def fake_exec(sql, params=(), **kwargs):
        calls.append((sql, params, kwargs))
        if sql.startswith("SELECT u.id"):
            return dict(row)
        return None
    monkeypatch.setattr(auth, "executar", fake_exec)
    user = auth.autenticar_usuario("A", "senha123")
    assert user["id"] == 7
    assert any("UPDATE Utilizadores SET senha_hash" in c[0] for c in calls)
    assert "senha_hash" not in user


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
    monkeypatch.setattr(auth, "executar", fake_exec)
    first = auth.obter_ou_criar_crianca(1, "Ana")
    state["owned"] = None
    second = auth.obter_ou_criar_crianca(2, "Ana")
    assert first != second


def test_object_authorization_matrix(monkeypatch):
    from utils import security
    child = {"utilizador_id": 10, "cuidador_id": 20}
    users = {10: "crianca", 20: "cuidador", 30: "profissional", 31: "profissional"}
    def fake_exec(sql, params=(), **kwargs):
        if "SELECT perfil FROM Utilizadores" in sql:
            return {"perfil": users.get(params[0])}
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
    assert not security.usuario_pode_acessar_crianca(30, "cuidador", 99)
    assert not security.usuario_pode_acessar_crianca(1, "admin", 99)


def test_session_expiration_and_revocation(monkeypatch):
    from modules import auth
    now = datetime.utcnow()
    row = {"id": 1, "nome": "A", "perfil": "crianca", "username": "a", "email": None, "senha_hash": "x", "deve_trocar_senha": 0, "crianca_id": 9, "ultima_atividade": (now - timedelta(minutes=31)).isoformat()}
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


def test_session_bound_child_listing_and_linking(monkeypatch):
    from modules import auth
    state = {"current": {"id": 10}, "users": {10: "cuidador", 11: "cuidador"}}
    def fake_exec(sql, params=(), **kwargs):
        if sql.startswith("SELECT perfil FROM Utilizadores"):
            return {"perfil": state["users"].get(params[0])}
        if "SELECT id, nome, data_nascimento FROM Criancas WHERE cuidador_id" in sql:
            return [{"id": 99, "nome": "A"}]
        return None
    class SessionState(dict):
        pass
    fake_st = type("Streamlit", (), {"session_state": SessionState(autenticado=True, usuario=state["current"])})
    import sys
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)
    monkeypatch.setattr(auth, "executar", fake_exec)
    assert auth.obter_criancas_do_usuario(10, "cuidador")
    assert auth.obter_criancas_do_usuario(11, "cuidador") == []


def test_sensitive_account_mutation_rejects_foreign_id(monkeypatch):
    from modules import auth
    import sys
    fake_st = type("Streamlit", (), {"session_state": {"autenticado": True, "usuario": {"id": 10}}})
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)
    monkeypatch.setattr(auth, "executar", lambda *args, **kwargs: None)
    assert auth.atualizar_usuario(11, "X", "x") == "Sessao invalida. Faca login novamente."
    assert auth.trocar_senha_obrigatoria(11, "nova123") == "Sessao invalida. Faca login novamente."


def test_user_controlled_values_are_escaped_before_raw_html():
    files = [
        "views/dashboard_cuidador/_crianca.py",
        "views/dashboard_cuidador/_hoje.py",
        "views/dashboard_cuidador/_historico.py",
        "views/dashboard_cuidador/_vinculos.py",
        "views/dashboard_cuidador/_perfil.py",
        "views/dashboard_cuidador/__init__.py",
        "views/dashboard_profissional/__init__.py",
        "views/dashboard_profissional/_painel.py",
        "views/dashboard_profissional/_exportacao.py",
        "views/dashboard_profissional/_insights.py",
        "views/dashboard_profissional/_pacientes.py",
        "views/dashboard_profissional/_perfil.py",
        "views/painel_crianca.py",
    ]
    for filename in files:
        source = Path(filename).read_text(encoding="utf-8")
        if "unsafe_allow_html=True" in source:
            assert "import html" in source, filename
            assert "html.escape" in source, filename


def test_streamlit_security_config_is_not_disabled():
    config = Path(".streamlit/config.toml").read_text(encoding="utf-8").lower()
    assert "enablexsrfprotection = false" not in config
    assert "enablecors = false" not in config
