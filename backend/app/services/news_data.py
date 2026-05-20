"""News and sentiment data adapters."""

from __future__ import annotations

import json
import os
import random
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

from backend.app.services.market_data import normalize_symbol


NEWSNOW_API_BASE = os.environ.get("NEWSNOW_API_BASE", "https://newsnow.busiyi.world").rstrip("/")
NEWSNOW_ENDPOINT = f"{NEWSNOW_API_BASE}/api/s"
NEWSNOW_DEFAULT_SOURCES = [
    ("cls-hot", "CLS"),
    ("wallstreetcn-hot", "Wallstreetcn"),
    ("thepaper", "The Paper"),
    ("baidu", "Baidu"),
    ("weibo", "Weibo"),
    ("zhihu", "Zhihu"),
    ("toutiao", "Toutiao"),
]
NEWSNOW_HEADERS = {
    "User-Agent": "Mozilla/5.0 QuantDash/1.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
}


def captured_at() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_sources(sources: str | None) -> list[tuple[str, str]]:
    if not sources:
        return NEWSNOW_DEFAULT_SOURCES

    source_names = dict(NEWSNOW_DEFAULT_SOURCES)
    selected = []
    for raw_source in sources.split(","):
        source_id = raw_source.strip()
        if source_id:
            selected.append((source_id, source_names.get(source_id, source_id)))
    return selected or NEWSNOW_DEFAULT_SOURCES


def read_json(url: str, encoding: str = "utf-8") -> dict[str, Any]:
    request = urllib.request.Request(url, headers=NEWSNOW_HEADERS)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode(encoding, "ignore"))


def fetch_newsnow_source(
    source_id: str,
    source_name: str,
) -> tuple[list[dict[str, Any]], str | None]:
    params = urllib.parse.urlencode({"id": source_id, "latest": "true"})
    url = f"{NEWSNOW_ENDPOINT}?{params}"
    data = read_json(url)
    status = data.get("status")
    if status not in {"success", "cache"}:
        raise RuntimeError(f"unexpected NewsNow status for {source_id}: {status}")

    updated_at = stringify(data.get("updatedTime"))
    rows = []
    seen_titles: set[str] = set()
    now = captured_at()
    for rank, item in enumerate(data.get("items", []), 1):
        title = stringify(item.get("title")).strip()
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        rows.append(
            {
                "id": stringify(item.get("id")) or f"{source_id}-{rank}",
                "title": title,
                "url": stringify(item.get("url")),
                "mobile_url": stringify(item.get("mobileUrl")),
                "source_id": source_id,
                "source": source_name,
                "source_name": source_name,
                "rank": rank,
                "updated_at": updated_at,
                "captured_at": now,
            }
        )
    return rows, status


def get_hot_news(sources: str | None = None, limit: int = 60) -> dict[str, Any]:
    selected_sources = parse_sources(sources)
    rows: list[dict[str, Any]] = []
    failed_sources: list[str] = []
    source_status: dict[str, str] = {}

    for index, (source_id, source_name) in enumerate(selected_sources):
        try:
            source_rows, status = fetch_newsnow_source(source_id, source_name)
            rows.extend(source_rows)
            source_status[source_id] = status or "success"
        except Exception:  # pylint: disable=broad-exception-caught
            failed_sources.append(source_id)

        if index < len(selected_sources) - 1:
            time.sleep(max(0.05, (100 + random.randint(-10, 20)) / 1000))

    bounded_limit = max(1, min(limit, 200))
    rows.sort(key=news_sort_key, reverse=True)
    payload_status = "ready" if rows else "unavailable"
    return {
        "source": "newsnow",
        "status": payload_status,
        "data": rows[:bounded_limit],
        "failed_sources": failed_sources,
        "source_status": source_status,
    }


def get_stock_news(symbol: str, limit: int = 30) -> dict[str, Any]:
    clean = normalize_symbol(symbol)
    try:
        stock_news_em = load_akshare_stock_news()
        frame = stock_news_em(symbol=clean)
    except Exception as error:  # pylint: disable=broad-exception-caught
        return {
            "symbol": clean,
            "source": "akshare.stock_news_em",
            "status": "unavailable",
            "message": str(error),
            "data": [],
        }

    rows = []
    now = captured_at()
    records = frame.to_dict("records") if hasattr(frame, "to_dict") else []
    for record in records:
        title = first_text(record, ["新闻标题", "title", "标题"])
        if not title:
            continue
        rows.append(
            {
                "symbol": clean,
                "title": title,
                "summary": first_text(record, ["新闻内容", "summary", "内容"]),
                "url": first_text(record, ["新闻链接", "url", "链接"]),
                "source": first_text(record, ["文章来源", "source", "来源"]) or "Eastmoney",
                "published_at": first_text(record, ["发布时间", "publish_time", "时间"]),
                "time": first_text(record, ["发布时间", "publish_time", "时间"]),
                "captured_at": now,
            }
        )

    bounded_limit = max(1, min(limit, 100))
    rows.sort(key=news_sort_key, reverse=True)
    return {
        "symbol": clean,
        "source": "akshare.stock_news_em",
        "status": "ready" if rows else "empty",
        "data": rows[:bounded_limit],
    }


def load_akshare_stock_news():
    # Import lazily so the API can still start and report an unavailable data source
    # if the optional provider is missing in a local environment.
    import akshare as ak  # pylint: disable=import-outside-toplevel

    return ak.stock_news_em


def first_text(record: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = record.get(key)
        text = stringify(value).strip()
        if text and text.lower() != "nan":
            return text
    return ""


def news_sort_key(item: dict[str, Any]) -> tuple[float, int]:
    timestamp = 0.0
    for key in ("published_at", "time", "updated_at", "captured_at"):
        parsed = parse_news_datetime(item.get(key))
        if parsed is not None:
            timestamp = parsed
            break
    rank = item.get("rank")
    return (timestamp, -int(rank) if isinstance(rank, int) else 0)


def parse_news_datetime(value: Any) -> float | None:
    text = stringify(value).strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    if " " in normalized and "T" not in normalized:
        normalized = normalized.replace(" ", "T", 1)
    try:
        return datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        return None


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
