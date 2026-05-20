"""Tushare provider adapter for reference and announcement data."""

from __future__ import annotations

from typing import Any

from backend.app.services.config import TUSHARE_TOKEN
from backend.app.services.reference_utils import infer_exchange, normalize_provider_date, utc_now


def tushare_status() -> dict[str, Any]:
    if not TUSHARE_TOKEN:
        return {
            "id": "tushare",
            "status": "not_configured",
            "required_env": "TUSHARE_TOKEN",
        }
    try:
        pro = tushare_client()
        pro.query("stock_basic", fields="ts_code,symbol,name", limit=1)
        return {"id": "tushare", "status": "ready"}
    except Exception as error:  # pylint: disable=broad-exception-caught
        return {"id": "tushare", "status": "unavailable", "error": str(error)}


def fetch_tushare_stock_profiles() -> list[dict[str, Any]]:
    pro = tushare_client()
    frame = pro.stock_basic(
        exchange="",
        list_status="L",
        fields="ts_code,symbol,name,area,industry,list_date",
    )
    rows = []
    for row in frame.to_dict("records"):
        symbol = str(row.get("symbol", "")).zfill(6)
        if len(symbol) != 6:
            continue
        rows.append(
            {
                "symbol": symbol,
                "name": str(row.get("name") or symbol),
                "exchange": infer_exchange(symbol),
                "industry": empty_to_none(row.get("industry")),
                "listed_at": normalize_provider_date(row.get("list_date")),
                "delisted_at": None,
                "pinyin": None,
                "source": "tushare.stock_basic",
                "updated_at": utc_now(),
            }
        )
    return rows


def fetch_tushare_announcements(symbol: str, limit: int = 30) -> dict[str, Any]:
    pro = tushare_client()
    ts_code = to_ts_code(symbol)
    frame = pro.anns(ts_code=ts_code)
    rows = []
    now = utc_now()
    for index, row in enumerate(frame.to_dict("records")):
        if index >= limit:
            break
        rows.append(
            {
                "symbol": symbol,
                "title": str(row.get("title") or ""),
                "summary": None,
                "source": "tushare.anns",
                "url": str(row.get("url") or ""),
                "published_at": normalize_provider_date(row.get("ann_date")),
                "type": "announcement",
                "captured_at": now,
            }
        )
    return {
        "symbol": symbol,
        "source": "tushare.anns",
        "status": "ready" if rows else "empty",
        "updated_at": now,
        "data": rows,
    }


def tushare_client():
    if not TUSHARE_TOKEN:
        raise RuntimeError("TUSHARE_TOKEN is not configured")
    import tushare as ts  # pylint: disable=import-outside-toplevel

    ts.set_token(TUSHARE_TOKEN)
    return ts.pro_api()


def to_ts_code(symbol: str) -> str:
    suffix = "SH" if symbol.startswith(("6", "9")) else "SZ"
    return f"{symbol}.{suffix}"


def empty_to_none(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None
