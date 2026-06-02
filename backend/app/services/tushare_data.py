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
    """Fetch the latest index weights via AkShare (China Securities Index)."""
    cache_key = f"akshare:index_members:{index_code}:{target_date}"
    cached = cache_get_json(cache_key)
    if cached is not None:
        return cached

    code = index_code.split(".", maxsplit=1)[0]
    ak = _load_akshare()
    frame = ak.index_stock_cons_weight_csindex(symbol=code)
    records = frame.to_dict("records") if hasattr(frame, "to_dict") else []
    if not records:
        return []

    rows = []
    for row in records:
        raw_code = str(row.get("成分券代码") or "")
        symbol = raw_code.split(".", maxsplit=1)[0].zfill(6)
        if len(symbol) != 6:
            continue
        weight_val = numeric(row.get("权重"))
        if weight_val is not None and weight_val > 1:
            weight_val = weight_val / 100.0
        rows.append(
            {
                "symbol": symbol,
                "name": str(row.get("成分券名称") or symbol),
                "exchange": infer_exchange(symbol),
                "listed_at": None,
                "source": "akshare.index_stock_cons_weight_csindex",
                "trade_date": normalize_provider_date(row.get("日期")),
                "weight": weight_val,
            }
        )
    cache_set_json(cache_key, rows, CACHE_TTL_SECONDS)
    return rows


def fetch_tushare_announcements(symbol: str, limit: int = 30) -> dict[str, Any]:
    ak = _load_akshare()
    rows: list[dict[str, Any]] = []
    now = utc_now()
    today = date.today()
    max_days = min(limit * 3, 90)
    for offset in range(max_days):
        check_date = today - timedelta(days=offset)
        if check_date.weekday() >= 5:
            continue
        date_str = check_date.strftime("%Y%m%d")
        try:
            frame = ak.stock_notice_report(symbol=symbol, date=date_str)
        except Exception:  # pylint: disable=broad-exception-caught
            continue
        day_records = frame.to_dict("records") if hasattr(frame, "to_dict") else []
        for row in day_records:
            rows.append(
                {
                    "symbol": symbol,
                    "title": str(row.get("公告标题") or row.get("标题") or ""),
                    "summary": None,
                    "source": "akshare.stock_notice_report",
                    "url": str(row.get("公告链接") or row.get("网址") or row.get("url") or ""),
                    "published_at": normalize_provider_date(
                        row.get("公告日期") or row.get("日期") or date_str
                    ),
                    "type": "announcement",
                    "captured_at": now,
                }
            )
            if len(rows) >= limit:
                break
        if len(rows) >= limit:
            break
    return {
        "symbol": symbol,
        "source": "akshare.stock_notice_report",
        "status": "ready" if rows else "empty",
        "updated_at": now,
        "data": rows,
    }


def fetch_tushare_daily_basic(symbol: str) -> dict[str, Any]:
    """Latest snapshot of valuation/turnover indicators via AkShare spot data."""
    ak = _load_akshare()
    frame = ak.stock_zh_a_spot_em()
    records = frame.to_dict("records") if hasattr(frame, "to_dict") else []
    for row in records:
        if str(row.get("代码") or "") == symbol:
            return {
                "symbol": symbol,
                "source": "akshare.stock_zh_a_spot_em",
                "status": "ready",
                "data": {
                    "trade_date": utc_now(),
                    "close": numeric(row.get("最新价")),
                    "pe": None,
                    "pe_ttm": numeric(row.get("市盈率-动态")),
                    "pb": numeric(row.get("市净率")),
                    "ps_ttm": None,
                    "dv_ttm": None,
                    "turnover_rate": numeric(row.get("换手率")),
                    "turnover_rate_f": None,
                    "total_mv": numeric(row.get("总市值")),
                    "circ_mv": numeric(row.get("流通市值")),
                    "total_share": None,
                    "float_share": None,
                },
            }
    return {
        "symbol": symbol,
        "data": None,
        "source": "akshare.stock_zh_a_spot_em",
        "status": "empty",
    }


def fetch_tushare_fina_indicator(symbol: str) -> dict[str, Any]:
    """Latest report period quality/growth metrics via AkShare financial analysis."""
    ak = _load_akshare()
    frame = ak.stock_financial_analysis_indicator_em(symbol=symbol, indicator="按报告期")
    records = frame.to_dict("records") if hasattr(frame, "to_dict") else []
    if not records:
        return {
            "symbol": symbol,
            "data": None,
            "source": "akshare.stock_financial_analysis_indicator_em",
            "status": "empty",
        }
    latest = records[0]
    return {
        "symbol": symbol,
        "source": "akshare.stock_financial_analysis_indicator_em",
        "status": "ready",
        "data": {
            "report_period": normalize_provider_date(latest.get("报告期")),
            "roe": numeric(latest.get("净资产收益率(%)")),
            "roe_waa": numeric(latest.get("加权净资产收益率(%)")),
            "roe_dt": None,
            "gross_margin": numeric(latest.get("销售毛利率(%)")),
            "netprofit_margin": numeric(latest.get("销售净利率(%)")),
            "debt_to_assets": numeric(latest.get("资产负债率(%)")),
            "revenue_yoy": numeric(latest.get("主营业务收入增长率(%)")),
            "netprofit_yoy": numeric(latest.get("净利润增长率(%)")),
            "assets_yoy": numeric(latest.get("总资产增长率(%)")),
        },
    }


def _load_akshare():
    import akshare as ak  # pylint: disable=import-outside-toplevel

    return ak


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


def empty_to_none(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None
