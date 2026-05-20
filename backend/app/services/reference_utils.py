"""Shared reference-data normalization helpers."""
# pylint: disable=duplicate-code

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def infer_exchange(symbol: str) -> str:
    clean = "".join(ch for ch in symbol if ch.isdigit())
    if clean.startswith(("6", "9")):
        return "SSE"
    if clean.startswith(("0", "2", "3")):
        return "SZSE"
    if clean.startswith(("4", "8")):
        return "BSE"
    return "UNKNOWN"


def normalize_provider_date(value: Any) -> str | None:
    text = stringify(value).strip()
    if not text:
        return None
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    if "T" in text:
        text = text.split("T", 1)[0]
    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError:
        return None


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
