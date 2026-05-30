"""Real A-share market data adapters backed by AkShare."""

from __future__ import annotations

import csv
import math
import re
import time
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Any, Literal

import requests


INDEXES = [
    ("000001", "上证指数"),
    ("399001", "深证成指"),
    ("399006", "创业板指"),
    ("000688", "科创50"),
]

KlineType = Literal["1min", "5day", "daily", "weekly", "monthly", "yearly"]
AdjustType = Literal["none", "qfq", "hfq"]


def normalize_symbol(symbol: str) -> str:
    clean = "".join(ch for ch in symbol if ch.isdigit())
    if len(clean) != 6:
        raise ValueError(f"invalid A-share symbol: {symbol}")
    return clean


def market_symbol(symbol: str) -> str:
    clean = normalize_symbol(symbol)
    if clean.startswith(("6", "9")):
        return f"sh{clean}"
    return f"sz{clean}"


def get_quote(symbol: str) -> dict[str, Any]:
    clean = normalize_symbol(symbol)
    try:
        quote = bid_ask_map(clean)
        info = individual_info_map(clean)
        return quote_payload(
            clean,
            quote,
            name=stringify(info.get("股票简称")) or clean,
            source="akshare.stock_bid_ask_em",
        )
    except Exception:  # pylint: disable=broad-exception-caught
        quote = sina_quote_map(clean)
        return quote_payload(
            clean,
            quote,
            name=stringify(quote.get("股票简称")) or clean,
            source="sina.hq",
            trade_date=stringify(quote.get("交易日期")) or None,
            trade_time=stringify(quote.get("交易时间")) or None,
        )


def quote_payload(
    symbol: str,
    quote: dict[str, Any],
    *,
    name: str,
    source: str,
    trade_date: str | None = None,
    trade_time: str | None = None,
) -> dict[str, Any]:
    previous_close = to_float(quote.get("昨收"))
    current = to_float(quote.get("最新"))
    change_amount = to_float(quote.get("涨跌"))
    if change_amount is None and current is not None and previous_close:
        change_amount = round(current - previous_close, 2)
    change_rate = to_float(quote.get("涨幅"))
    if change_rate is None and change_amount is not None and previous_close:
        change_rate = round(change_amount / previous_close * 100, 2)

    return {
        "symbol": symbol,
        "name": name,
        "current_price": current,
        "change_rate": change_rate,
        "change_amount": change_amount,
        "volume": to_int(quote.get("总手")),
        "turnover": to_float(quote.get("金额")),
        "high": to_float(quote.get("最高")),
        "low": to_float(quote.get("最低")),
        "open": to_float(quote.get("今开")),
        "previous_close": previous_close,
        "pe_ttm": None,
        "pb": None,
        "turnover_rate": to_float(quote.get("换手")),
        "trade_date": trade_date or date.today().isoformat(),
        "trade_time": trade_time or datetime.now().strftime("%H:%M:%S"),
        "source": source,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }


def ten_year_cutoff() -> date:
    return date.today() - timedelta(days=3653)


def aggregate_period(
    rows: list[dict[str, Any]],
    period: Literal["weekly", "monthly", "yearly"],
) -> list[dict[str, Any]]:
    buckets: dict[tuple[int, ...], list[dict[str, Any]]] = {}
    for row in rows:
        row_date = date.fromisoformat(row["date"])
        if period == "weekly":
            year, week, _ = row_date.isocalendar()
            key = (year, week)
        elif period == "monthly":
            key = (row_date.year, row_date.month)
        else:
            key = (row_date.year,)
        buckets.setdefault(key, []).append(row)

    aggregated: list[dict[str, Any]] = []
    for _, items in sorted(buckets.items()):
        first = items[0]
        last = items[-1]
        previous = aggregated[-1]["close"] if aggregated else first["open"]
        close = last["close"]
        aggregated.append(
            {
                "date": last["date"],
                "open": first["open"],
                "close": close,
                "high": max(item["high"] for item in items),
                "low": min(item["low"] for item in items),
                "volume": sum(item["volume"] for item in items),
                "turnover": None,
                "amplitude": None,
                "change_rate": round((close - previous) / previous * 100, 2) if previous else 0,
                "change_amount": round(close - previous, 2),
                "turnover_rate": None,
            }
        )
    return aggregated


def get_kline(
    symbol: str,
    ktype: KlineType = "daily",
    adjust: AdjustType = "none",
) -> dict[str, Any]:
    clean = normalize_symbol(symbol)
    ak = load_akshare()
    ak_adjust = "" if adjust == "none" else adjust

    if ktype in ("1min", "5day"):
        return _get_minute_kline(clean, ktype, ak)

    cutoff = ten_year_cutoff()
    try:
        frame = with_retries(
            lambda: ak.stock_zh_a_hist(
                symbol=clean,
                period="daily",
                start_date=cutoff.strftime("%Y%m%d"),
                end_date=date.today().strftime("%Y%m%d"),
                adjust=ak_adjust,
            )
        )
        source = "akshare.stock_zh_a_hist"
    except Exception:  # pylint: disable=broad-exception-caught
        frame = with_retries(
            lambda: ak.stock_zh_a_hist_tx(
                symbol=market_symbol(clean),
                start_date=cutoff.strftime("%Y%m%d"),
                end_date=date.today().strftime("%Y%m%d"),
                adjust=ak_adjust,
            )
        )
        source = "akshare.stock_zh_a_hist_tx"

    rows = [
        {
            "date": stringify(first_value(item, "日期", "date")),
            "open": to_float(first_value(item, "开盘", "open")),
            "close": to_float(first_value(item, "收盘", "close")),
            "high": to_float(first_value(item, "最高", "high")),
            "low": to_float(first_value(item, "最低", "low")),
            "volume": to_int(first_value(item, "成交量", "volume", "amount")) or 0,
            "turnover": to_float(first_value(item, "成交额", "turnover")),
            "amplitude": to_float(first_value(item, "振幅")),
            "change_rate": to_float(first_value(item, "涨跌幅")),
            "change_amount": to_float(first_value(item, "涨跌额")),
            "turnover_rate": to_float(first_value(item, "换手率")),
        }
        for item in frame.to_dict("records")
        if stringify(first_value(item, "日期", "date"))
        and date.fromisoformat(stringify(first_value(item, "日期", "date"))) >= cutoff
    ]
    data = aggregate_period(rows, ktype) if ktype in {"weekly", "monthly", "yearly"} else rows

    return {
        "symbol": clean,
        "type": ktype,
        "adjust": adjust,
        "source": source,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "data": data,
    }


def _get_minute_kline(symbol: str, ktype: str, ak: Any) -> dict[str, Any]:
    """Fetch 1-minute K-line data. For '5day' mode, fetch last 5 trading days."""
    try:
        frame = with_retries(
            lambda: ak.stock_zh_a_hist_min_em(symbol=symbol, period="1", adjust="")
        )
        source = "akshare.stock_zh_a_hist_min_em"
    except Exception:  # pylint: disable=broad-exception-caught
        frame = with_retries(
            lambda: ak.stock_zh_a_minute(symbol=market_symbol(symbol), period="1", adjust="")
        )
        source = "akshare.stock_zh_a_minute"

    rows = [
        {
            "date": stringify(first_value(item, "时间", "day")),
            "open": to_float(first_value(item, "开盘", "open")),
            "close": to_float(first_value(item, "收盘", "close")),
            "high": to_float(first_value(item, "最高", "high")),
            "low": to_float(first_value(item, "最低", "low")),
            "volume": to_int(first_value(item, "成交量", "volume")) or 0,
            "turnover": to_float(first_value(item, "成交额", "amount")),
            "amplitude": None,
            "change_rate": None,
            "change_amount": None,
            "turnover_rate": None,
        }
        for item in frame.to_dict("records")
        if stringify(first_value(item, "时间", "day"))
    ]

    if ktype == "1min":
        # Keep the latest trading day returned by the provider. This avoids
        # filtering everything out on holidays, after-hours, or date-skewed dev machines.
        latest_date = max((r["date"][:10] for r in rows), default="")
        rows = [r for r in rows if r["date"].startswith(latest_date)]
    else:
        # 5day: keep last 5 trading days
        unique_dates = sorted(set(r["date"][:10] for r in rows), reverse=True)
        keep_dates = set(unique_dates[:5])
        rows = [r for r in rows if r["date"][:10] in keep_dates]

    return {
        "symbol": symbol,
        "type": ktype,
        "adjust": "none",
        "source": source,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "data": rows,
    }


def get_indexes() -> dict[str, Any]:
    ak = load_akshare()
    try:
        frame = ak.stock_zh_index_spot_em(symbol="沪深重要指数")
        source = "akshare.stock_zh_index_spot_em"
    except Exception:  # pylint: disable=broad-exception-caught
        frame = ak.stock_zh_index_spot_sina()
        source = "akshare.stock_zh_index_spot_sina"
    rows_by_symbol = {
        provider_symbol(row.get("代码")): row
        for row in frame.to_dict("records")
    }
    data = [
        {
            "symbol": symbol,
            "name": stringify(rows_by_symbol.get(symbol, {}).get("名称")) or name,
            "value": to_float(rows_by_symbol.get(symbol, {}).get("最新价")),
            "change_amount": to_float(rows_by_symbol.get(symbol, {}).get("涨跌额")),
            "change_rate": to_float(rows_by_symbol.get(symbol, {}).get("涨跌幅")),
            "volume": to_float(rows_by_symbol.get(symbol, {}).get("成交量")),
            "turnover": to_float(rows_by_symbol.get(symbol, {}).get("成交额")),
        }
        for symbol, name in INDEXES
        if symbol in rows_by_symbol
    ]
    return {
        "source": source,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "data": data,
    }


def search_stocks(query: str) -> dict[str, Any]:
    text = query.strip().lower()
    if not text:
        return {"source": "akshare.stock_info_a_code_name", "query": query, "data": []}

    data = []
    for row in stock_code_name_rows():
        symbol = stringify(row.get("code"))
        name = stringify(row.get("name"))
        if text in symbol.lower() or text in name.lower():
            data.append({"symbol": symbol, "name": name})
        if len(data) >= 20:
            break

    return {
        "source": "akshare.stock_info_a_code_name",
        "query": query,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "data": data,
    }


def get_order_book(symbol: str) -> dict[str, Any]:
    clean = normalize_symbol(symbol)
    labels = ["一", "二", "三", "四", "五"]
    try:
        quote = bid_ask_map(clean)
        source = "akshare.stock_bid_ask_em"
    except Exception:  # pylint: disable=broad-exception-caught
        quote = sina_quote_map(clean)
        source = "sina.hq"

    bids = [
        {
            "level": f"买{labels[index]}",
            "price": to_float(quote.get(f"buy_{index + 1}")),
            "volume": to_int(quote.get(f"buy_{index + 1}_vol")),
        }
        for index in range(5)
    ]
    asks = [
        {
            "level": f"卖{labels[index]}",
            "price": to_float(quote.get(f"sell_{index + 1}")),
            "volume": to_int(quote.get(f"sell_{index + 1}_vol")),
        }
        for index in range(5)
    ]

    return {
        "symbol": clean,
        "source": source,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "data": {"asks": list(reversed(asks)), "bids": bids},
    }


def get_financials(symbol: str) -> dict[str, Any]:
    clean = normalize_symbol(symbol)
    quote = get_quote(clean)
    return {
        "symbol": clean,
        "source": quote.get("source"),
        "updated_at": "实时 quote 不包含完整财务指标",
        "data": {
            "pe_ttm": quote.get("pe_ttm"),
            "pb": quote.get("pb"),
            "roe": None,
            "gross_margin": None,
        },
    }


def unavailable_dataset(symbol: str | None, source: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "source": source,
        "status": "unavailable",
        "data": [],
    }
    if symbol is not None:
        payload["symbol"] = normalize_symbol(symbol)
    return payload


def bid_ask_map(symbol: str) -> dict[str, Any]:
    ak = load_akshare()
    frame = ak.stock_bid_ask_em(symbol=normalize_symbol(symbol))
    return {stringify(row.get("item")): row.get("value") for row in frame.to_dict("records")}


def individual_info_map(symbol: str) -> dict[str, Any]:
    ak = load_akshare()
    frame = ak.stock_individual_info_em(symbol=normalize_symbol(symbol))
    return {stringify(row.get("item")): row.get("value") for row in frame.to_dict("records")}


def sina_quote_map(symbol: str) -> dict[str, Any]:
    market_code = market_symbol(symbol)
    response = requests.get(
        f"https://hq.sinajs.cn/list={market_code}",
        headers={"Referer": "https://finance.sina.com.cn"},
        timeout=5,
    )
    response.raise_for_status()
    response.encoding = "gb18030"
    match = re.search(rf'var hq_str_{market_code}="(.*)";', response.text)
    if match is None:
        raise ValueError(f"empty Sina quote response for {symbol}")
    values = next(csv.reader([match.group(1)]))
    if len(values) < 32 or not values[0]:
        raise ValueError(f"incomplete Sina quote response for {symbol}")

    quote = {
        "股票简称": values[0],
        "今开": values[1],
        "昨收": values[2],
        "最新": values[3],
        "最高": values[4],
        "最低": values[5],
        "金额": values[9],
        "总手": values[8],
        "交易日期": values[30],
        "交易时间": values[31],
    }
    for index in range(5):
        bid_offset = 10 + index * 2
        ask_offset = 20 + index * 2
        quote[f"buy_{index + 1}_vol"] = values[bid_offset]
        quote[f"buy_{index + 1}"] = values[bid_offset + 1]
        quote[f"sell_{index + 1}_vol"] = values[ask_offset]
        quote[f"sell_{index + 1}"] = values[ask_offset + 1]
    return quote


def provider_symbol(value: Any) -> str:
    digits = "".join(ch for ch in stringify(value) if ch.isdigit())
    return digits[-6:]


@lru_cache(maxsize=1)
def stock_code_name_rows() -> tuple[dict[str, Any], ...]:
    ak = load_akshare()
    frame = ak.stock_info_a_code_name()
    return tuple(frame.to_dict("records"))


def load_akshare():
    import akshare as ak  # pylint: disable=import-outside-toplevel

    return ak


def with_retries(factory, attempts: int = 3, delay: float = 0.25):
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return factory()
        except Exception as error:  # pylint: disable=broad-exception-caught
            last_error = error
            if attempt < attempts - 1:
                time.sleep(delay * (attempt + 1))
    if last_error is not None:
        raise last_error
    raise RuntimeError("data provider call failed")


def first_value(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value is not None:
            return value
    return None


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result):
        return None
    return result


def to_int(value: Any) -> int | None:
    number = to_float(value)
    return int(number) if number is not None else None


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
