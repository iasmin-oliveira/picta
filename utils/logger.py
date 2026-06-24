"""
PICTA — utils/logger.py
Logger estruturado centralizado.

Uso:
    from utils.logger import get_logger
    log = get_logger(__name__)
    log.info("Usuário autenticado", extra={"usuario_id": 42})
    log.warning("Tentativa de login falhou", extra={"username": "x"})
    log.error("Erro ao executar query", exc_info=True)

Configuração via variáveis de ambiente:
    LOG_LEVEL  — DEBUG | INFO | WARNING | ERROR  (padrão: INFO)
    LOG_FILE   — caminho do arquivo de log       (padrão: stdout apenas)
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler


# ── Formato estruturado ───────────────────────────────────────────────────────
_FMT = "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s"
_DATE = "%Y-%m-%dT%H:%M:%S"

# ── Estado do setup ───────────────────────────────────────────────────────────
_configured = False


def _setup() -> None:
    """Configura o logger raiz uma única vez."""
    global _configured
    if _configured:
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    formatter = logging.Formatter(_FMT, datefmt=_DATE)

    # Handler stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)

    handlers: list[logging.Handler] = [stdout_handler]

    # Handler arquivo (opcional)
    log_file = os.getenv("LOG_FILE", "")
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    root = logging.getLogger("picta")
    root.setLevel(level)
    # Evita duplicação se já tiver handlers (ex: hot-reload do Streamlit)
    if not root.handlers:
        for h in handlers:
            root.addHandler(h)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger filho do namespace 'picta'.

    Args:
        name: Normalmente __name__ do módulo chamador.

    Returns:
        logging.Logger configurado.
    """
    _setup()
    # Normaliza para picta.views.login, picta.database.db, etc.
    if not name.startswith("picta"):
        name = f"picta.{name.lstrip('.')}"
    return logging.getLogger(name)
