"""Intraday minute bars and same-day trade-print aggregations."""
# pylint: disable=duplicate-code

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.app.services.market_data import (
    first_value,
    load_akshare,
    market_symbol,
    normalize_symbol,
    stringify,
    to_float,
    to_int,
    with_retries,
)
from backend.app.services.reference_utils import utc_now


def get_intraday(symbol: str) -> dict[str, Any]:
    """Latest trading day's 1-minute bars for the intraday/分时 chart."""
    clean = normalize_symbol(symbol)
    ak = load_akshare()
    try:
        frame = with_retries(
            lambda: ak.stock_zh_a_hist_min_em(symbol=clean, period="1", adjust="")
        )
        source = "akshare.stock_zh_a_hist_min_em"
    except Exception as primary_error:  # pylint: disable=broad-exception-caught
        try:
            frame = with_retries(
                lambda: ak.stock_zh_a_minute(symbol=market_symbol(clean), period="1", adjust="")
            )
            source = "akshare.stock_zh_a_minute"
        except Exception as fallback_error:  # pylint: disable=broad-exception-caught
            return {
                "symbol": clean,
                "source": "akshare.intraday",
                "status": "unavailable",
                "message": f"{primary_error} / {fallback_error}",
                "data": [],
            }

    rows = []
    for item in frame.to_dict("records"):
        timestamp = stringify(first_value(item, "时间", "day"))
        if not timestamp:
            continue
        rows.append(
            {
                "time": timestamp,
                "open": to_float(first_value(item, "开盘", "open")),
                "close": to_float(first_value(item, "收盘", "close")),
                "high": to_float(first_value(item, "最高", "high")),
                "low": to_float(first_value(item, "最低", "low")),
                "volume": to_int(first_value(item, "成交量", "volume")),
                "turnover": to_float(first_value(item, "成交额", "amount")),
            }
        )

    latest_day = max((row["time"][:10] for row in rows), default="")
    rows = [row for row in rows if row["time"].startswith(latest_day)]

    return {
        "symbol": clean,
        "source": source,
        "status": "ready" if rows else "empty",
        "trade_date": latest_day or None,
        "updated_at": utc_now(),
        "data": rows,
    }


def get_trade_prints(symbol: str, limit: int = 60) -> dict[str, Any]:
    """Same-day trade prints aggregated by AkShare.

    A-share Tick data normally requires a paid feed. The first version uses
    the publicly available aggregated prints (`stock_intraday_em`) so the
    dashboard 逐笔成交 panel can show real values, while we keep the contract
    open for a future Tick-level data source.
    """
    clean = normalize_symbol(symbol)
    ak = load_akshare()
    try:
        frame = with_retries(lambda: ak.stock_intraday_em(symbol=clean))
        source = "akshare.stock_intraday_em"
    except Exception as error:  # pylint: disable=broad-exception-caught
        return {
            "symbol": clean,
            "source": "akshare.stock_intraday_em",
            "status": "unavailable",
            "message": str(error),
            "data": [],
        }

    bounded_limit = max(1, min(limit, 200))
    rows = []
    for item in frame.to_dict("records"):
        time_value = stringify(first_value(item, "时间", "成交时间", "time"))
        if not time_value:
            continue
        side_value = stringify(first_value(item, "买卖盘性质", "性质", "类型", "side"))
        rows.append(
            {
                "time": format_time(time_value),
                "price": to_float(first_value(item, "成交价", "价格", "price")),
                "volume": to_int(first_value(item, "手数", "成交量", "volume")),
                "turnover": to_float(first_value(item, "成交额", "amount")),
                "side": normalize_side(side_value),
            }
        )

    rows.reverse()
    rows = rows[:bounded_limit]

    return {
        "symbol": clean,
        "source": source,
        "status": "ready" if rows else "empty",
        "updated_at": utc_now(),
        "data": rows,
    }


def normalize_side(value: str) -> str:
    text = value.strip()
    if not text:
        return "中性"
    if text in {"买", "买入", "B", "BUY", "主买"}:
        return "买入"
    if text in {"卖", "卖出", "S", "SELL", "主卖"}:
        return "卖出"
    return text


def format_time(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if " " in text:
        text = text.split(" ", 1)[1]
    if "T" in text:
        text = text.split("T", 1)[1]
    try:
        # Some providers return seconds with sub-second components which we
        # truncate to keep the dashboard tidy.
        return datetime.strptime(text[:8], "%H:%M:%S").strftime("%H:%M:%S")
    except ValueError:
        return text
