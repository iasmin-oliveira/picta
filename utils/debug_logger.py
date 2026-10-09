
import logging
import os
import sys

LOG_DIR = "logs"

logger = logging.getLogger("picta_debug")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        handler = logging.FileHandler(
            os.path.join(LOG_DIR, "picta_debug.log"),
            encoding="utf-8",
        )
    except OSError:
        handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def log_debug(message):
    logger.debug(message)

def log_error(message):
    logger.error(message)
