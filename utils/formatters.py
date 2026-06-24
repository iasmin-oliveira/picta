"""Small presentation formatters used by dashboards and exports."""

from __future__ import annotations

import datetime
import re
import unicodedata
from typing import Any


def parse_local_datetime(value: Any) -> datetime.datetime | None:
    if not value:
        return None
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, datetime.date):
        return datetime.datetime.combine(value, datetime.time.min)
    try:
        return datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def format_date_br(value: Any) -> str:
    if isinstance(value, datetime.datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, datetime.date):
        return value.strftime("%d/%m/%Y")

    dt = parse_local_datetime(value)
    return dt.strftime("%d/%m/%Y") if dt else str(value or "")


def format_datetime_br(value: Any, sep: str = " às ") -> str:
    dt = parse_local_datetime(value)
    return dt.strftime(f"%d/%m/%Y{sep}%H:%M") if dt else str(value or "")


def format_time(value: Any) -> str:
    dt = parse_local_datetime(value)
    return dt.strftime("%H:%M") if dt else ""


def format_period_br(start: Any, end: Any) -> str:
    return f"{format_date_br(start)} a {format_date_br(end)}"


def filename_date(value: Any) -> str:
    if isinstance(value, datetime.datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, datetime.date):
        return value.strftime("%Y-%m-%d")
    dt = parse_local_datetime(value)
    return dt.strftime("%Y-%m-%d") if dt else str(value or "")


def safe_filename(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", ascii_text).strip("_")
    return cleaned or "picta"
