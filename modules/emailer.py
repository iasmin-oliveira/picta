"""Simple SMTP email helpers for account recovery."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Optional

from utils.logger import get_logger

_log = get_logger(__name__)


def _secret(name: str, default: str = "") -> str:
    try:
        import streamlit as st

        email_cfg = st.secrets.get("email", {})
        if hasattr(email_cfg, "get") and email_cfg.get(name):
            return str(email_cfg.get(name))
    except Exception:
        pass
    return os.getenv(f"PICTA_EMAIL_{name.upper()}", default)


def email_configurado() -> bool:
    return bool(_secret("host") and _secret("from"))


def enviar_senha_temporaria(destino: str, nome: str, senha_temporaria: str) -> Optional[str]:
    if not email_configurado():
        return "Envio de email nao configurado."

    host = _secret("host")
    port = int(_secret("port", "587"))
    user = _secret("user")
    password = _secret("password")
    sender = _secret("from")
    use_tls = _secret("tls", "true").lower() != "false"

    msg = EmailMessage()
    msg["Subject"] = "PICTA - senha temporaria"
    msg["From"] = sender
    msg["To"] = destino
    msg.set_content(
        "\n".join(
            [
                f"Ola, {nome}.",
                "",
                "Recebemos uma solicitacao de recuperacao de senha no PICTA.",
                f"Sua senha temporaria e: {senha_temporaria}",
                "",
                "Ao entrar, o sistema pedira a troca por uma nova senha.",
                "Se voce nao solicitou isso, avise o responsavel pelo sistema.",
            ]
        )
    )

    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            if use_tls:
                smtp.starttls()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)
        return None
    except Exception as exc:
        _log.warning("Falha ao enviar email de recuperacao: %s", exc)
        return "Nao foi possivel enviar o email de recuperacao agora."
