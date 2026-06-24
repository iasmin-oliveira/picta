"""Database access for PICTA.

The app uses Neon/PostgreSQL when a database URL is configured in Streamlit
secrets or environment variables. Otherwise it falls back to the local SQLite
database used during development.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional

from utils.debug_logger import log_debug
from utils.logger import get_logger

_log = get_logger(__name__)

CREATE_TEST_USER = os.getenv("CREATE_TEST_USER", "false").lower() == "true"
SQLITE_PATH = Path(__file__).resolve().parent.parent / "picta.db"
_INITIALIZED = False
_PG_POOL = None
_PG_POOL_LOCK = threading.Lock()

PICTOGRAMAS_SEED = [
    ("FELIZ", "emocao", "😊"),
    ("TRISTE", "emocao", "😢"),
    ("BRAVO", "emocao", "😠"),
    ("ASSUSTADO", "emocao", "😨"),
    ("CALMO", "emocao", "😌"),
    ("CHORANDO", "emocao", "😭"),
    ("SURPRESO", "emocao", "😲"),
    ("CANSADO", "emocao", "😴"),
    ("AMADO", "emocao", "🥰"),
    ("ANSIOSO", "emocao", "😰"),
    ("ORGULHOSO", "emocao", "🌟"),
    ("CONFUSO", "emocao", "😕"),
    ("COMER", "acao", "🍽️"),
    ("BRINCAR", "acao", "🎮"),
    ("DORMIR", "acao", "🛌"),
    ("CHUTAR BOLA", "acao", "⚽"),
    ("LER", "acao", "📖"),
    ("DESENHAR", "acao", "✏️"),
    ("DANÇAR", "acao", "💃"),
    ("ASSISTIR TV", "acao", "📺"),
    ("PASSEAR", "acao", "🚶"),
    ("CANTAR", "acao", "🎤"),
    ("ÁGUA", "necessidade", "💧"),
    ("BANHEIRO", "necessidade", "🚽"),
    ("AJUDA", "necessidade", "🙋"),
    ("DESCANSO", "necessidade", "🛋️"),
    ("REMÉDIO", "necessidade", "💊"),
    ("ABRAÇO", "necessidade", "🤗"),
    ("SILÊNCIO", "necessidade", "🤫"),
    ("MÚSICA", "necessidade", "🎵"),
    ("BANHO", "necessidade", "🛁"),
    ("FOME", "necessidade", "🍎"),
    ("SEDE", "necessidade", "🥤"),
    ("FRIO", "necessidade", "🧥"),
    ("CALOR", "necessidade", "🌡️"),
]


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def _get_database_url() -> Optional[str]:
    try:
        import streamlit as st

        neon = st.secrets.get("neon", {})
        url = neon.get("database_url") if hasattr(neon, "get") else None
        if url:
            return str(url)
    except Exception:
        pass
    return os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")


def _usar_postgres() -> bool:
    return bool(_get_database_url())


def _get_pg_conn():
    import psycopg2.pool

    global _PG_POOL
    database_url = _get_database_url()
    if not database_url:
        raise RuntimeError("URL do banco Neon nao configurada.")

    if _PG_POOL is None:
        with _PG_POOL_LOCK:
            if _PG_POOL is None:
                _PG_POOL = psycopg2.pool.SimpleConnectionPool(
                    1,
                    8,
                    database_url,
                    connect_timeout=5,
                )
    for _ in range(2):
        conn = _PG_POOL.getconn()
        if not getattr(conn, "closed", False):
            return conn
        _PG_POOL.putconn(conn, close=True)

    raise RuntimeError("Nao foi possivel obter uma conexao ativa com o Neon.")


def _release_pg_conn(conn, close: bool = False) -> None:
    if not conn:
        return
    if _PG_POOL is None:
        conn.close()
        return
    _PG_POOL.putconn(conn, close=close or bool(getattr(conn, "closed", False)))


def _get_sqlite_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _inicializar_pg() -> None:
    conn = _get_pg_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS Utilizadores (
                id         SERIAL PRIMARY KEY,
                nome       TEXT NOT NULL,
                perfil     TEXT NOT NULL,
                username   TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                criado_em  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS Criancas (
                id              SERIAL PRIMARY KEY,
                nome            TEXT NOT NULL,
                data_nascimento DATE,
                cuidador_id     INTEGER REFERENCES Utilizadores(id),
                utilizador_id   INTEGER REFERENCES Utilizadores(id)
            );
            CREATE TABLE IF NOT EXISTS Pictogramas (
                id        SERIAL PRIMARY KEY,
                nome      TEXT NOT NULL,
                categoria TEXT NOT NULL,
                emoji     TEXT,
                imagem    TEXT
            );
            CREATE TABLE IF NOT EXISTS Registos_Interacao (
                id            SERIAL PRIMARY KEY,
                crianca_id    INTEGER NOT NULL REFERENCES Criancas(id),
                pictograma_id INTEGER NOT NULL REFERENCES Pictogramas(id),
                registado_em  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS Sessoes (
                token            TEXT PRIMARY KEY,
                usuario_id       INTEGER NOT NULL REFERENCES Utilizadores(id),
                expira_em        TIMESTAMP NOT NULL,
                ultima_atividade TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                criado_em        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS Vinculos (
                id         SERIAL PRIMARY KEY,
                usuario_id INTEGER NOT NULL REFERENCES Utilizadores(id),
                crianca_id INTEGER NOT NULL REFERENCES Criancas(id),
                criado_em  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(usuario_id, crianca_id)
            );
            """
        )

        for sql in (
            "ALTER TABLE Criancas ALTER COLUMN cuidador_id DROP NOT NULL;",
            "ALTER TABLE Criancas ADD COLUMN IF NOT EXISTS utilizador_id INTEGER REFERENCES Utilizadores(id);",
            "ALTER TABLE Sessoes ADD COLUMN IF NOT EXISTS ultima_atividade TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
            """
            DELETE FROM Criancas a USING Criancas b
            WHERE a.utilizador_id IS NOT NULL
              AND a.utilizador_id = b.utilizador_id
              AND a.id > b.id;
            """,
            """
            DO $$
            DECLARE r RECORD;
            BEGIN
                FOR r IN
                    SELECT conname FROM pg_constraint
                    WHERE conrelid = 'utilizadores'::regclass
                      AND contype = 'c'
                      AND pg_get_constraintdef(oid) ILIKE '%perfil%'
                LOOP
                    EXECUTE 'ALTER TABLE Utilizadores DROP CONSTRAINT ' || r.conname;
                END LOOP;
            END $$;
            """,
        ):
            try:
                cur.execute(sql)
                conn.commit()
            except Exception:
                conn.rollback()

        cur.execute(
            """
            WITH canonical AS (
                SELECT nome, MIN(id) AS keep_id
                FROM Pictogramas
                GROUP BY nome
            ),
            dupes AS (
                SELECT p.id, c.keep_id
                FROM Pictogramas p
                JOIN canonical c ON c.nome = p.nome
                WHERE p.id <> c.keep_id
            )
            UPDATE Registos_Interacao ri
            SET pictograma_id = d.keep_id
            FROM dupes d
            WHERE ri.pictograma_id = d.id;
            WITH canonical AS (
                SELECT nome, MIN(id) AS keep_id
                FROM Pictogramas
                GROUP BY nome
            )
            DELETE FROM Pictogramas p
            USING canonical c
            WHERE p.nome = c.nome
              AND p.id <> c.keep_id;
            """
        )
        conn.commit()

        cur.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_pictogramas_nome_unique
                ON Pictogramas(nome);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_criancas_utilizador_unique
                ON Criancas(utilizador_id)
                WHERE utilizador_id IS NOT NULL;
            CREATE INDEX IF NOT EXISTS idx_criancas_cuidador
                ON Criancas(cuidador_id);
            CREATE INDEX IF NOT EXISTS idx_registos_crianca_data
                ON Registos_Interacao(crianca_id, registado_em DESC);
            CREATE INDEX IF NOT EXISTS idx_vinculos_usuario
                ON Vinculos(usuario_id);
            CREATE INDEX IF NOT EXISTS idx_sessoes_usuario
                ON Sessoes(usuario_id);
            """
        )

        if CREATE_TEST_USER:
            _seed_demo_pg(cur)

        for nome, categoria, emoji in PICTOGRAMAS_SEED:
            cur.execute(
                """
                INSERT INTO Pictogramas(nome, categoria, emoji)
                SELECT %s, %s, %s
                WHERE NOT EXISTS (
                    SELECT 1 FROM Pictogramas WHERE nome = %s
                )
                """,
                (nome, categoria, emoji, nome),
            )

        conn.commit()
        cur.close()
    finally:
        _release_pg_conn(conn)


def _seed_demo_pg(cur) -> None:
    cur.execute("SELECT id FROM Utilizadores WHERE username = %s", ("cuidador_teste",))
    if cur.fetchone():
        return
    cur.execute(
        "INSERT INTO Utilizadores(nome, perfil, username, senha_hash) VALUES(%s,%s,%s,%s) RETURNING id",
        ("Maria Silva", "responsavel", "cuidador_teste", hash_senha("senha123")),
    )
    resp_id = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO Utilizadores(nome, perfil, username, senha_hash) VALUES(%s,%s,%s,%s) RETURNING id",
        ("Joao Silva", "crianca", "joao", hash_senha("joao123")),
    )
    crianca_uid = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO Criancas(nome, data_nascimento, cuidador_id, utilizador_id) VALUES(%s,%s,%s,%s)",
        ("Joao Silva", "2017-03-15", resp_id, crianca_uid),
    )


def _inicializar_sqlite() -> None:
    conn = _get_sqlite_conn()
    try:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS Utilizadores (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                nome       TEXT NOT NULL,
                perfil     TEXT NOT NULL,
                username   TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                criado_em  DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS Criancas (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                nome            TEXT NOT NULL,
                data_nascimento DATE,
                cuidador_id     INTEGER REFERENCES Utilizadores(id),
                utilizador_id   INTEGER REFERENCES Utilizadores(id)
            );
            CREATE TABLE IF NOT EXISTS Pictogramas (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                nome      TEXT NOT NULL,
                categoria TEXT NOT NULL,
                emoji     TEXT,
                imagem    TEXT
            );
            CREATE TABLE IF NOT EXISTS Registos_Interacao (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                crianca_id    INTEGER NOT NULL REFERENCES Criancas(id),
                pictograma_id INTEGER NOT NULL REFERENCES Pictogramas(id),
                registado_em  DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS Sessoes (
                token            TEXT PRIMARY KEY,
                usuario_id       INTEGER NOT NULL REFERENCES Utilizadores(id),
                expira_em        DATETIME NOT NULL,
                ultima_atividade DATETIME DEFAULT CURRENT_TIMESTAMP,
                criado_em        DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS Vinculos (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL REFERENCES Utilizadores(id),
                crianca_id INTEGER NOT NULL REFERENCES Criancas(id),
                criado_em  DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(usuario_id, crianca_id)
            );
            """
        )

        _migrar_sqlite(cur)

        cur.executescript(
            """
            UPDATE Registos_Interacao
            SET pictograma_id = (
                SELECT MIN(p2.id)
                FROM Pictogramas p2
                WHERE p2.nome = (
                    SELECT p3.nome
                    FROM Pictogramas p3
                    WHERE p3.id = Registos_Interacao.pictograma_id
                )
            )
            WHERE pictograma_id IN (
                SELECT id
                FROM Pictogramas
                WHERE id NOT IN (
                    SELECT MIN(id) FROM Pictogramas GROUP BY nome
                )
            );
            DELETE FROM Pictogramas
            WHERE id NOT IN (
                SELECT MIN(id) FROM Pictogramas GROUP BY nome
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_pictogramas_nome_unique
                ON Pictogramas(nome);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_criancas_utilizador_unique
                ON Criancas(utilizador_id)
                WHERE utilizador_id IS NOT NULL;
            CREATE INDEX IF NOT EXISTS idx_criancas_cuidador
                ON Criancas(cuidador_id);
            CREATE INDEX IF NOT EXISTS idx_registos_crianca_data
                ON Registos_Interacao(crianca_id, registado_em DESC);
            CREATE INDEX IF NOT EXISTS idx_vinculos_usuario
                ON Vinculos(usuario_id);
            CREATE INDEX IF NOT EXISTS idx_sessoes_usuario
                ON Sessoes(usuario_id);
            """
        )

        if CREATE_TEST_USER:
            _seed_demo_sqlite(cur)

        for nome, categoria, emoji in PICTOGRAMAS_SEED:
            cur.execute("SELECT id FROM Pictogramas WHERE nome = ?", (nome,))
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO Pictogramas(nome, categoria, emoji) VALUES(?,?,?)",
                    (nome, categoria, emoji),
                )

        conn.commit()
    finally:
        conn.close()


def _migrar_sqlite(cur: sqlite3.Cursor) -> None:
    create_sql = cur.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='Utilizadores'"
    ).fetchone()
    if create_sql and "CHECK" in create_sql[0].upper() and "perfil" in create_sql[0].lower():
        cur.executescript(
            """
            PRAGMA foreign_keys = OFF;
            CREATE TABLE IF NOT EXISTS Utilizadores_new (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                nome       TEXT NOT NULL,
                perfil     TEXT NOT NULL,
                username   TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                criado_em  DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO Utilizadores_new SELECT id,nome,perfil,username,senha_hash,criado_em
            FROM Utilizadores;
            DROP TABLE Utilizadores;
            ALTER TABLE Utilizadores_new RENAME TO Utilizadores;
            PRAGMA foreign_keys = ON;
            """
        )

    for tabela, coluna, definicao in (
        ("Criancas", "utilizador_id", "INTEGER REFERENCES Utilizadores(id)"),
        ("Sessoes", "ultima_atividade", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
    ):
        cols = [r[1] for r in cur.execute(f"PRAGMA table_info({tabela})").fetchall()]
        if coluna not in cols:
            cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")

    cur.execute(
        """
        DELETE FROM Criancas
        WHERE utilizador_id IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id) FROM Criancas
              WHERE utilizador_id IS NOT NULL
              GROUP BY utilizador_id
          )
        """
    )

    if cur.execute("SELECT COUNT(*) FROM Pictogramas WHERE emoji LIKE '&#%'").fetchone()[0]:
        cur.execute("DELETE FROM Pictogramas")


def _seed_demo_sqlite(cur: sqlite3.Cursor) -> None:
    cur.execute("SELECT id FROM Utilizadores WHERE username = ?", ("cuidador_teste",))
    if cur.fetchone():
        return
    cur.execute(
        "INSERT INTO Utilizadores(nome, perfil, username, senha_hash) VALUES(?,?,?,?)",
        ("Maria Silva", "responsavel", "cuidador_teste", hash_senha("senha123")),
    )
    resp_id = cur.lastrowid
    cur.execute(
        "INSERT INTO Utilizadores(nome, perfil, username, senha_hash) VALUES(?,?,?,?)",
        ("Joao Silva", "crianca", "joao", hash_senha("joao123")),
    )
    crianca_uid = cur.lastrowid
    cur.execute(
        "INSERT INTO Criancas(nome, data_nascimento, cuidador_id, utilizador_id) VALUES(?,?,?,?)",
        ("Joao Silva", "2017-03-15", resp_id, crianca_uid),
    )


def inicializar_db() -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return
    if _usar_postgres():
        _inicializar_pg()
    else:
        _inicializar_sqlite()
    _INITIALIZED = True


def _ensure_initialized() -> None:
    if not _INITIALIZED:
        inicializar_db()


def executar(
    query: str,
    params: tuple = (),
    fetchone: bool = False,
    fetchall: bool = False,
    commit: bool = False,
) -> Any:
    """Executa uma query no banco ativo usando placeholders no formato SQLite."""
    _ensure_initialized()

    if _usar_postgres():
        import psycopg2.extras

        max_attempts = 1 if commit else 2
        for attempt in range(max_attempts):
            conn = None
            cur = None
            close_conn = False
            try:
                conn = _get_pg_conn()
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur.execute(query.replace("?", "%s"), params)
                result: Any = None
                if fetchone:
                    row = cur.fetchone()
                    result = dict(row) if row else None
                elif fetchall:
                    rows = cur.fetchall()
                    result = [dict(row) for row in rows]
                if commit:
                    conn.commit()
                return result
            except (psycopg2.OperationalError, psycopg2.InterfaceError):
                close_conn = True
                if conn and not getattr(conn, "closed", True):
                    try:
                        conn.rollback()
                    except Exception:
                        close_conn = True
                if attempt + 1 >= max_attempts:
                    raise
            except Exception:
                if conn and not getattr(conn, "closed", True):
                    conn.rollback()
                raise
            finally:
                if cur is not None:
                    try:
                        cur.close()
                    except Exception:
                        close_conn = True
                if conn is not None:
                    _release_pg_conn(conn, close=close_conn)

    conn = _get_sqlite_conn()
    try:
        cur = conn.execute(query, params)
        result = None
        if fetchone:
            row = cur.fetchone()
            result = dict(row) if row else None
        elif fetchall:
            result = [dict(row) for row in cur.fetchall()]
        if commit:
            conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


log_debug("database/db.py carregado")
