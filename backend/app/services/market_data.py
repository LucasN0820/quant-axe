"""Real A-share market data adapters.

The first production backend version uses Sina public endpoints because they
work without API keys and cover the PRD's MVP quote/K-line/index needs.
"""

from __future__ import annotations

import json
import re
import urllib.request
from datetime import date
from typing import Any, Literal


SINA_QUOTE = "https://hq.sinajs.cn/list="
SINA_KLINE = "https://quotes.sina.cn/cn/api/jsonp.php/var%20K=/KC_MarketDataService.getKLineData"

INDEXES = [
    ("000001", "上证指数", "s_sh000001"),
    ("399001", "深证成指", "s_sz399001"),
    ("399006", "创业板指", "s_sz399006"),
    ("000688", "科创50", "s_sh000688"),
]


def normalize_symbol(symbol: str) -> str:
    clean = "".join(ch for ch in symbol if ch.isdigit())
    if len(clean) != 6:
        raise ValueError(f"invalid A-share symbol: {symbol}")
    return clean


def sina_symbol(symbol: str) -> str:
    clean = normalize_symbol(symbol)
    prefix = "sh" if clean.startswith(("5", "6", "9")) else "sz"
    return f"{prefix}{clean}"


def read_text(url: str, encoding: str = "utf-8") -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 QuantDash/1.0",
            "Referer": "https://finance.sina.com.cn/",
        },
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.read().decode(encoding, "ignore")


def parse_hq_payload(text: str) -> list[str]:
    match = re.search(r'="(.*)";', text, re.S)
    if not match:
        raise RuntimeError("invalid Sina quote payload")
    payload = match.group(1)
    if not payload:
        raise RuntimeError("empty Sina quote payload")
    return payload.split(",")


def get_quote(symbol: str) -> dict[str, Any]:
    clean = normalize_symbol(symbol)
    fields = parse_hq_payload(read_text(f"{SINA_QUOTE}{sina_symbol(clean)}", "gbk"))
    previous_close = float(fields[2])
    current = float(fields[3])
    change_amount = round(current - previous_close, 2)
    change_rate = round(change_amount / previous_close * 100, 2) if previous_close else 0

    return {
        "symbol": clean,
        "name": fields[0],
        "current_price": current,
        "change_rate": change_rate,
        "change_amount": change_amount,
        "volume": int(float(fields[8])),
        "turnover": float(fields[9]),
        "high": float(fields[4]),
        "low": float(fields[5]),
        "open": float(fields[1]),
        "previous_close": previous_close,
        "pe_ttm": None,
        "pb": None,
        "turnover_rate": None,
        "trade_date": fields[30] if len(fields) > 30 else None,
        "trade_time": fields[31] if len(fields) > 31 else None,
        "source": "sina",
    }


def aggregate_weekly(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for row in rows:
        year, week, _ = date.fromisoformat(row["date"]).isocalendar()
        buckets.setdefault((year, week), []).append(row)

    weekly: list[dict[str, Any]] = []
    for _, items in sorted(buckets.items()):
        first = items[0]
        last = items[-1]
        previous = weekly[-1]["close"] if weekly else first["open"]
        close = last["close"]
        weekly.append(
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
    return weekly


def get_kline(symbol: str, ktype: Literal["daily", "weekly"] = "daily") -> dict[str, Any]:
    clean = normalize_symbol(symbol)
    url = f"{SINA_KLINE}?symbol={sina_symbol(clean)}&scale=240&ma=no&datalen=2000"
    text = read_text(url)
    match = re.search(r"var K=\((.*)\);?", text, re.S)
    if not match:
        raise RuntimeError("invalid Sina K-line payload")

    raw_rows = json.loads(match.group(1))
    rows = [
        {
            "date": item["d"],
            "open": float(item["o"]),
            "close": float(item["c"]),
            "high": float(item["h"]),
            "low": float(item["l"]),
            "volume": int(float(item["v"])),
            "turnover": None,
            "amplitude": None,
            "change_rate": None,
            "change_amount": None,
            "turnover_rate": None,
        }
        for item in raw_rows[-160:]
    ]
    data = aggregate_weekly(rows)[-120:] if ktype == "weekly" else rows[-120:]

    return {
        "symbol": clean,
        "type": ktype,
        "source": "sina",
        "data": data,
    }


def get_indexes() -> dict[str, Any]:
    data = []
    for symbol, name, sina_code in INDEXES:
        fields = parse_hq_payload(read_text(f"{SINA_QUOTE}{sina_code}", "gbk"))
        data.append(
            {
                "symbol": symbol,
                "name": name,
                "value": float(fields[1]),
                "change_amount": float(fields[2]),
                "change_rate": float(fields[3]),
                "volume": float(fields[4]),
                "turnover": float(fields[5]),
            }
        )
    return {"source": "sina", "data": data}
