"""
PICTA — database/db.py

Abstração de banco de dados:
  - LOCAL  → SQLite  (desenvolvimento local, sem configuração)
  - CLOUD  → PostgreSQL via Neon  (Streamlit Cloud, via st.secrets)

Detecção automática: se existir [neon] em st.secrets → PostgreSQL.
Caso contrário → SQLite.
"""

import hashlib
import os
import sqlite3

import streamlit as st

PICTOGRAMAS_SEED = [
    ('FELIZ',       'emocao',      '😊'),
    ('TRISTE',      'emocao',      '😢'),
    ('BRAVO',       'emocao',      '😠'),
    ('ASSUSTADO',   'emocao',      '😨'),
    ('CALMO',       'emocao',      '😌'),
    ('CHORANDO',    'emocao',      '😭'),
    ('SURPRESO',    'emocao',      '😲'),
    ('CANSADO',     'emocao',      '😴'),
    ('COMER',       'acao',        '🍽️'),
    ('BRINCAR',     'acao',        '🎮'),
    ('DORMIR',      'acao',        '🛌'),
    ('CHUTAR BOLA', 'acao',        '⚽'),
    ('LER',         'acao',        '📖'),
    ('DESENHAR',    'acao',        '✏️'),
    ('DANÇAR',      'acao',        '💃'),
    ('ASSISTIR TV', 'acao',        '📺'),
    ('ÁGUA',        'necessidade', '💧'),
    ('BANHEIRO',    'necessidade', '🚽'),
    ('AJUDA',       'necessidade', '🙋'),
    ('DESCANSO',    'necessidade', '🛋️'),
    ('REMÉDIO',     'necessidade', '💊'),
    ('ABRAÇO',      'necessidade', '🤗'),
    ('SILÊNCIO',    'necessidade', '🤫'),
    ('MÚSICA',      'necessidade', '🎵'),
]


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()


# ══════════════════════════════════════════════════════════
#  DETECÇÃO DE AMBIENTE
# ══════════════════════════════════════════════════════════

def _usar_postgres() -> bool:
    try:
        return "neon" in st.secrets
    except Exception:
        return False


# ══════════════════════════════════════════════════════════
#  POSTGRESQL — Neon (Produção / Streamlit Cloud)
# ══════════════════════════════════════════════════════════

def _get_pg_conn():
    """Conexão via DATABASE_URL do Neon (mais simples e robusta)."""
    import psycopg2
    import psycopg2.extras
    url = st.secrets["neon"]["database_url"]
    conn = psycopg2.connect(url)
    return conn


def _inicializar_pg():
    conn = _get_pg_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Utilizadores (
            id         SERIAL PRIMARY KEY,
            nome       TEXT NOT NULL,
            perfil     TEXT NOT NULL CHECK(perfil IN ('crianca','cuidador')),
            username   TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            criado_em  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS Criancas (
            id              SERIAL PRIMARY KEY,
            nome            TEXT NOT NULL,
            data_nascimento DATE,
            cuidador_id     INTEGER NOT NULL REFERENCES Utilizadores(id)
        );
        CREATE TABLE IF NOT EXISTS Pictogramas (
            id        SERIAL PRIMARY KEY,
            nome      TEXT NOT NULL,
            categoria TEXT NOT NULL CHECK(categoria IN ('emocao','acao','necessidade')),
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
            token      TEXT PRIMARY KEY,
            usuario_id INTEGER NOT NULL REFERENCES Utilizadores(id),
            criado_em  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expira_em  TIMESTAMP NOT NULL
        );
    """)

    # Seed utilizadores
    cur.execute("SELECT id FROM Utilizadores WHERE username='cuidador_teste'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO Utilizadores(nome,perfil,username,senha_hash) VALUES(%s,%s,%s,%s) RETURNING id",
            ('Maria Silva', 'cuidador', 'cuidador_teste', hash_senha('senha123'))
        )
        cuidador_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO Utilizadores(nome,perfil,username,senha_hash) VALUES(%s,%s,%s,%s)",
            ('João Silva', 'crianca', 'joao', hash_senha('joao123'))
        )
        cur.execute(
            "INSERT INTO Criancas(nome,data_nascimento,cuidador_id) VALUES(%s,%s,%s)",
            ('João Silva', '2017-03-15', cuidador_id)
        )

    # Seed pictogramas
    cur.execute("SELECT id FROM Pictogramas LIMIT 1")
    if not cur.fetchone():
        cur.executemany(
            "INSERT INTO Pictogramas(nome,categoria,emoji) VALUES(%s,%s,%s)",
            PICTOGRAMAS_SEED
        )

    conn.commit()
    cur.close()
    conn.close()


# ══════════════════════════════════════════════════════════
#  SQLITE — Local (Desenvolvimento)
# ══════════════════════════════════════════════════════════

_SQLITE_PATH = os.path.join(os.path.dirname(__file__), '..', 'picta.db')


def _get_sqlite_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_SQLITE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _inicializar_sqlite():
    conn = _get_sqlite_conn()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS Utilizadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
            perfil TEXT NOT NULL CHECK(perfil IN ('crianca','cuidador')),
            username TEXT UNIQUE NOT NULL, senha_hash TEXT NOT NULL,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS Criancas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
            data_nascimento DATE, cuidador_id INTEGER NOT NULL,
            FOREIGN KEY(cuidador_id) REFERENCES Utilizadores(id)
        );
        CREATE TABLE IF NOT EXISTS Pictogramas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
            categoria TEXT NOT NULL CHECK(categoria IN ('emocao','acao','necessidade')),
            emoji TEXT, imagem TEXT
        );
        CREATE TABLE IF NOT EXISTS Registos_Interacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crianca_id INTEGER NOT NULL, pictograma_id INTEGER NOT NULL,
            registado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(crianca_id) REFERENCES Criancas(id),
            FOREIGN KEY(pictograma_id) REFERENCES Pictogramas(id)
        );
        CREATE TABLE IF NOT EXISTS Sessoes (
            token TEXT PRIMARY KEY, usuario_id INTEGER NOT NULL,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP, expira_em DATETIME NOT NULL,
            FOREIGN KEY(usuario_id) REFERENCES Utilizadores(id)
        );
    """)

    # Migração: HTML entities → emoji Unicode
    if cur.execute("SELECT COUNT(*) FROM Pictogramas WHERE emoji LIKE '&#%'").fetchone()[0]:
        cur.execute("PRAGMA foreign_keys = OFF")
        cur.execute("DELETE FROM Pictogramas")
        cur.executemany("INSERT INTO Pictogramas(nome,categoria,emoji) VALUES(?,?,?)", PICTOGRAMAS_SEED)
        cur.execute("PRAGMA foreign_keys = ON")

    if not cur.execute("SELECT id FROM Utilizadores WHERE username='cuidador_teste'").fetchone():
        cur.execute(
            "INSERT INTO Utilizadores(nome,perfil,username,senha_hash) VALUES(?,?,?,?)",
            ('Maria Silva', 'cuidador', 'cuidador_teste', hash_senha('senha123'))
        )
        cuidador_id = cur.lastrowid
        cur.execute(
            "INSERT INTO Utilizadores(nome,perfil,username,senha_hash) VALUES(?,?,?,?)",
            ('João Silva', 'crianca', 'joao', hash_senha('joao123'))
        )
        cur.execute(
            "INSERT INTO Criancas(nome,data_nascimento,cuidador_id) VALUES(?,?,?)",
            ('João Silva', '2017-03-15', cuidador_id)
        )

    if not cur.execute("SELECT id FROM Pictogramas LIMIT 1").fetchone():
        cur.executemany("INSERT INTO Pictogramas(nome,categoria,emoji) VALUES(?,?,?)", PICTOGRAMAS_SEED)

    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════
#  API PÚBLICA
# ══════════════════════════════════════════════════════════

def inicializar_db():
    if _usar_postgres():
        _inicializar_pg()
    else:
        _inicializar_sqlite()


def executar(query: str, params: tuple = (), fetchone=False, fetchall=False, commit=False):
    """Executa query no banco ativo. Converte ? → %s para PostgreSQL automaticamente."""
    if _usar_postgres():
        import psycopg2.extras
        conn = _get_pg_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query.replace('?', '%s'), params)
        result = None
        if fetchone:
            row = cur.fetchone()
            result = dict(row) if row else None
        elif fetchall:
            rows = cur.fetchall()
            result = [dict(r) for r in rows] if rows else []
        if commit:
            conn.commit()
        cur.close()
        conn.close()
        return result
    else:
        conn = _get_sqlite_conn()
        cur = conn.execute(query, params)
        result = None
        if fetchone:
            row = cur.fetchone()
            result = dict(row) if row else None
        elif fetchall:
            result = [dict(r) for r in cur.fetchall()]
        if commit:
            conn.commit()
        conn.close()
        return result
