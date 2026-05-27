"""Tushare provider adapter for reference, announcement, and financial data."""
# pylint: disable=duplicate-code

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Any

from backend.app.services.config import CACHE_TTL_SECONDS, TUSHARE_TOKEN
from backend.app.services.reference_utils import infer_exchange, normalize_provider_date, utc_now
from backend.app.services.storage import cache_get_json, cache_set_json


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


def fetch_tushare_index_members(index_code: str, target_date: str) -> list[dict[str, Any]]:
    """Fetch the latest index weights at or before target_date without looking ahead."""
    cache_key = f"tushare:index_members:{index_code}:{target_date}"
    cached = cache_get_json(cache_key)
    if cached is not None:
        return cached

    pro = tushare_client()
    end = date.fromisoformat(target_date)
    start = end - timedelta(days=400)
    frame = pro.index_weight(
        index_code=index_code,
        start_date=start.strftime("%Y%m%d"),
        end_date=end.strftime("%Y%m%d"),
    )
    records = frame.to_dict("records") if hasattr(frame, "to_dict") else []
    if not records:
        return []

    latest_trade_date = max(str(row.get("trade_date") or "") for row in records)
    rows = []
    for row in records:
        if str(row.get("trade_date") or "") != latest_trade_date:
            continue
        symbol = str(row.get("con_code") or "").split(".", maxsplit=1)[0].zfill(6)
        if len(symbol) != 6:
            continue
        rows.append(
            {
                "symbol": symbol,
                "name": str(row.get("name") or symbol),
                "exchange": infer_exchange(symbol),
                "listed_at": None,
                "source": "tushare.index_weight",
                "trade_date": normalize_provider_date(latest_trade_date),
                "weight": numeric(row.get("weight")),
            }
        )
    cache_set_json(cache_key, rows, CACHE_TTL_SECONDS)
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


def fetch_tushare_daily_basic(symbol: str) -> dict[str, Any]:
    """Latest snapshot of valuation/turnover indicators from Tushare daily_basic."""
    pro = tushare_client()
    ts_code = to_ts_code(symbol)
    end = date.today().strftime("%Y%m%d")
    start = (date.today() - timedelta(days=14)).strftime("%Y%m%d")
    frame = pro.daily_basic(
        ts_code=ts_code,
        start_date=start,
        end_date=end,
        fields=(
            "ts_code,trade_date,close,turnover_rate,turnover_rate_f,"
            "pe,pe_ttm,pb,ps_ttm,dv_ttm,total_share,float_share,"
            "free_share,total_mv,circ_mv"
        ),
    )
    records = frame.to_dict("records") if hasattr(frame, "to_dict") else []
    if not records:
        return {"symbol": symbol, "data": None, "source": "tushare.daily_basic", "status": "empty"}
    latest = records[0]
    return {
        "symbol": symbol,
        "source": "tushare.daily_basic",
        "status": "ready",
        "data": {
            "trade_date": normalize_provider_date(latest.get("trade_date")),
            "close": numeric(latest.get("close")),
            "pe": numeric(latest.get("pe")),
            "pe_ttm": numeric(latest.get("pe_ttm")),
            "pb": numeric(latest.get("pb")),
            "ps_ttm": numeric(latest.get("ps_ttm")),
            "dv_ttm": numeric(latest.get("dv_ttm")),
            "turnover_rate": numeric(latest.get("turnover_rate")),
            "turnover_rate_f": numeric(latest.get("turnover_rate_f")),
            "total_mv": numeric(latest.get("total_mv")),
            "circ_mv": numeric(latest.get("circ_mv")),
            "total_share": numeric(latest.get("total_share")),
            "float_share": numeric(latest.get("float_share")),
        },
    }


def fetch_tushare_fina_indicator(symbol: str) -> dict[str, Any]:
    """Latest report period quality/growth metrics from Tushare fina_indicator."""
    pro = tushare_client()
    ts_code = to_ts_code(symbol)
    frame = pro.fina_indicator(
        ts_code=ts_code,
        fields=(
            "ts_code,end_date,roe,roe_waa,roe_dt,grossprofit_margin,"
            "netprofit_margin,debt_to_assets,or_yoy,netprofit_yoy,assets_yoy"
        ),
    )
    records = frame.to_dict("records") if hasattr(frame, "to_dict") else []
    if not records:
        return {
            "symbol": symbol,
            "data": None,
            "source": "tushare.fina_indicator",
            "status": "empty",
        }
    latest = records[0]
    return {
        "symbol": symbol,
        "source": "tushare.fina_indicator",
        "status": "ready",
        "data": {
            "report_period": normalize_provider_date(latest.get("end_date")),
            "roe": numeric(latest.get("roe")),
            "roe_waa": numeric(latest.get("roe_waa")),
            "roe_dt": numeric(latest.get("roe_dt")),
            "gross_margin": numeric(latest.get("grossprofit_margin")),
            "netprofit_margin": numeric(latest.get("netprofit_margin")),
            "debt_to_assets": numeric(latest.get("debt_to_assets")),
            "revenue_yoy": numeric(latest.get("or_yoy")),
            "netprofit_yoy": numeric(latest.get("netprofit_yoy")),
            "assets_yoy": numeric(latest.get("assets_yoy")),
        },
    }


def numeric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result):
        return None
    return result


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
