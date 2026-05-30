"""Financial metrics service combining daily valuation and financial indicators via AkShare."""

from __future__ import annotations

from typing import Any

from backend.app.services.market_data import normalize_symbol
from backend.app.services.reference_utils import utc_now
from backend.app.services.storage import save_raw_payload, upsert_financial_metrics


def get_financial_metrics(symbol: str) -> dict[str, Any]:
    """Return combined valuation, quality, and growth metrics for one symbol."""

    clean = normalize_symbol(symbol)

    daily_payload = safe_fetch(clean, "daily_basic")
    indicator_payload = safe_fetch(clean, "fina_indicator")

    daily_data = daily_payload.get("data") if daily_payload else None
    indicator_data = indicator_payload.get("data") if indicator_payload else None

    metrics = merge_metrics(clean, daily_data, indicator_data)
    persist_metrics(clean, indicator_data, daily_data)

    statuses = {
        "daily_basic": daily_payload.get("status") if daily_payload else "unavailable",
        "fina_indicator": indicator_payload.get("status") if indicator_payload else "unavailable",
    }
    overall = "ready" if metrics["pe_ttm"] is not None or metrics["roe"] is not None else "empty"

    return {
        "symbol": clean,
        "source": "akshare.stock_zh_a_spot_em+stock_financial_analysis_indicator_em",
        "status": overall,
        "providers": statuses,
        "updated_at": utc_now(),
        "data": metrics,
    }


def safe_fetch(symbol: str, dataset: str) -> dict[str, Any]:
    from backend.app.services.tushare_data import (  # pylint: disable=import-outside-toplevel
        fetch_tushare_daily_basic,
        fetch_tushare_fina_indicator,
    )

    fetcher = (
        fetch_tushare_daily_basic if dataset == "daily_basic" else fetch_tushare_fina_indicator
    )
    try:
        return fetcher(symbol)
    except Exception as error:  # pylint: disable=broad-exception-caught
        return {
            "symbol": symbol,
            "source": "akshare" if dataset == "daily_basic" else "akshare",
            "status": "unavailable",
            "message": str(error),
            "data": None,
        }


def merge_metrics(
    symbol: str,
    daily_data: dict[str, Any] | None,
    indicator_data: dict[str, Any] | None,
) -> dict[str, Any]:
    daily_data = daily_data or {}
    indicator_data = indicator_data or {}
    return {
        "symbol": symbol,
        "trade_date": daily_data.get("trade_date"),
        "report_period": indicator_data.get("report_period"),
        "pe_ttm": daily_data.get("pe_ttm"),
        "pe": daily_data.get("pe"),
        "pb": daily_data.get("pb"),
        "ps_ttm": daily_data.get("ps_ttm"),
        "dv_ttm": daily_data.get("dv_ttm"),
        "turnover_rate": daily_data.get("turnover_rate"),
        "total_mv": daily_data.get("total_mv"),
        "circ_mv": daily_data.get("circ_mv"),
        "roe": indicator_data.get("roe"),
        "roe_waa": indicator_data.get("roe_waa"),
        "gross_margin": indicator_data.get("gross_margin"),
        "netprofit_margin": indicator_data.get("netprofit_margin"),
        "debt_to_assets": indicator_data.get("debt_to_assets"),
        "revenue_yoy": indicator_data.get("revenue_yoy"),
        "netprofit_yoy": indicator_data.get("netprofit_yoy"),
    }


def persist_metrics(
    symbol: str,
    indicator_data: dict[str, Any] | None,
    daily_data: dict[str, Any] | None,
) -> None:
    rows: list[dict[str, Any]] = []
    now = utc_now()
    if indicator_data and indicator_data.get("report_period"):
        rows.append(
            {
                "symbol": symbol,
                "report_period": indicator_data["report_period"],
                "pe_ttm": (daily_data or {}).get("pe_ttm"),
                "pb": (daily_data or {}).get("pb"),
                "roe": indicator_data.get("roe"),
                "gross_margin": indicator_data.get("gross_margin"),
                "source": "akshare.stock_financial_analysis_indicator_em",
                "updated_at": now,
            }
        )
    if daily_data and daily_data.get("trade_date"):
        rows.append(
            {
                "symbol": symbol,
                "report_period": daily_data["trade_date"],
                "pe_ttm": daily_data.get("pe_ttm"),
                "pb": daily_data.get("pb"),
                "roe": None,
                "gross_margin": None,
                "source": "akshare.stock_zh_a_spot_em",
                "updated_at": now,
            }
        )

    if not rows:
        return

    try:
        upsert_financial_metrics(rows)
        save_raw_payload("akshare", "financial_metrics", rows, symbol)
    except Exception:  # pylint: disable=broad-exception-caught
        # Persistence is best-effort; the API still returns the in-memory
        # payload so the frontend can render valuation cards immediately.
        pass


def empty_payload() -> dict[str, Any]:
    return {
        "symbol": None,
        "trade_date": None,
        "report_period": None,
        "pe_ttm": None,
        "pe": None,
        "pb": None,
        "ps_ttm": None,
        "dv_ttm": None,
        "turnover_rate": None,
        "total_mv": None,
        "circ_mv": None,
        "roe": None,
        "roe_waa": None,
        "gross_margin": None,
        "netprofit_margin": None,
        "debt_to_assets": None,
        "revenue_yoy": None,
        "netprofit_yoy": None,
    }
