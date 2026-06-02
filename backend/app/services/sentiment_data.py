"""Hot keywords / sentiment heatmap derived from real news streams."""
# pylint: disable=duplicate-code

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from backend.app.services.news_data import get_hot_news
from backend.app.services.storage import insert_hot_keywords, save_raw_payload


# Words that show up frequently in Chinese financial headlines but carry no
# investment signal. Filtering them keeps the cloud focused on real topics.
STOPWORDS = frozenset(
    [
        "今天",
        "今日",
        "最新",
        "重要",
        "公告",
        "新闻",
        "发布",
        "全文",
        "速递",
        "解读",
        "财联社",
        "华尔街见闻",
        "澎湃新闻",
        "百度热搜",
        "微博",
        "知乎",
        "今日头条",
        "财经",
        "市场",
        "中国",
        "全球",
        "行业",
        "公司",
        "数据",
        "分析",
        "报道",
        "记者",
        "回应",
        "表示",
        "称",
        "据悉",
        "突发",
        "重磅",
        "多少",
        "如何",
        "为何",
    ]
)

WORD_PATTERN = re.compile(r"[\u4e00-\u9fff]{2,5}")
MIN_WORD_OCCURRENCES = 2
MAX_RESULT_KEYWORDS = 50


def captured_at() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_hot_keywords(limit: int = 30) -> dict[str, Any]:
    """Build a sentiment word cloud from the latest hot news headlines.

    The implementation deliberately stays simple so that the data center can
    ship a real signal without pulling in an NLP toolkit. Once a richer
    sentiment model is available the function can be replaced without changing
    the API contract.
    """

    bounded_limit = max(1, min(limit, MAX_RESULT_KEYWORDS))
    news_payload = get_hot_news(limit=120)
    items = news_payload.get("data") or []
    if not items:
        return {
            "source": "news_collector.r2.derived",
            "status": "unavailable" if news_payload.get("status") == "unavailable" else "empty",
            "data": [],
            "captured_at": captured_at(),
        }

    counter: Counter[str] = Counter()
    word_sources: dict[str, set[str]] = {}
    for item in items:
        title = str(item.get("title") or "").strip()
        source = str(item.get("source_id") or item.get("source") or "")
        if not title:
            continue
        for token in WORD_PATTERN.findall(title):
            if token in STOPWORDS:
                continue
            counter[token] += 1
            word_sources.setdefault(token, set()).add(source)

    if not counter:
        return {
            "source": "news_collector.r2.derived",
            "status": "empty",
            "data": [],
            "captured_at": captured_at(),
        }

    top = counter.most_common(bounded_limit)
    max_freq = max(freq for _, freq in top) or 1
    now = captured_at()
    rows = [
        {
            "word": word,
            "heat": round(freq / max_freq * 100, 2),
            "frequency": freq,
            "sources": sorted(word_sources.get(word, set())),
            "captured_at": now,
        }
        for word, freq in top
        if freq >= MIN_WORD_OCCURRENCES
    ]

    try:
        insert_hot_keywords(rows)
        save_raw_payload("news_collector.r2", "hot_keywords", rows)
    except Exception:  # pylint: disable=broad-exception-caught
        pass

    return {
        "source": "news_collector.r2.derived",
        "status": "ready" if rows else "empty",
        "captured_at": now,
        "data": rows,
    }
