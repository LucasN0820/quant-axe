"""News and sentiment data adapters."""
# pylint: disable=duplicate-code

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.app.services.market_data import normalize_symbol
from backend.app.services.news_r2 import get_hot_news_payload
from backend.app.services.storage import insert_news_items, save_raw_payload


def captured_at() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_hot_news(sources: str | None = None, limit: int = 60) -> dict[str, Any]:
    """Serve hot news from the SQLite snapshot uploaded by news-collector."""

    return get_hot_news_payload(sources, limit)


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
    try:
        insert_news_items(rows, "stock_news")
        save_raw_payload("akshare", "stock_news_em", rows, clean)
    except Exception:  # pylint: disable=broad-exception-caught
        pass
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
    if text.isdigit():
        number = int(text)
        if number > 10_000_000_000:
            number = number // 1000
        return float(number)
    normalized = text.replace("Z", "+00:00")
    if " " in normalized and "T" not in normalized:
        normalized = normalized.replace(" ", "T", 1)
    try:
        return datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        return None


def normalize_news_datetime(value: Any) -> str | None:
    timestamp = parse_news_datetime(value)
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
