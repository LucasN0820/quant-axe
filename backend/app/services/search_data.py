"""Combined search index for stocks, indexes, and ETFs."""
# pylint: disable=duplicate-code

from __future__ import annotations

from functools import lru_cache
from threading import Lock
from typing import Any

from backend.app.services.market_data import load_akshare, provider_symbol, stringify
from backend.app.services.reference_utils import infer_exchange, utc_now
from backend.app.services.storage import cache_get_json, cache_set_json


SEARCH_RESULT_LIMIT = 30
SEARCH_INDEX_CACHE_KEY = "search:universe:v1"
SEARCH_INDEX_STALE_CACHE_KEY = "search:universe:v1:stale"
SEARCH_INDEX_CACHE_TTL_SECONDS = 86_400
SEARCH_INDEX_STALE_TTL_SECONDS = 604_800
MINIMUM_COMPLETE_STOCK_COUNT = 1_000
SEARCH_INDEX_BUILD_LOCK = Lock()


def search_universe(query: str, limit: int = 20) -> dict[str, Any]:
    """Search across A-share stocks (incl. BSE), market indexes, and ETFs.

    The dataset is built once per process via `lru_cache` and rebuilt on
    AkShare connectivity recovery by clearing the cache from the scheduler.
    """
    text = query.strip()
    rows = lookup(text, limit)
    return {
        "source": "akshare.search_universe",
        "status": "ready",
        "query": query,
        "updated_at": utc_now(),
        "data": rows,
    }


def lookup(text: str, limit: int) -> list[dict[str, Any]]:
    if not text:
        return []
    bounded_limit = max(1, min(limit, SEARCH_RESULT_LIMIT))
    needle = text.lower()
    digits = "".join(ch for ch in text if ch.isdigit())

    matches: list[tuple[int, dict[str, Any]]] = []
    for record in search_index():
        score = score_entry(record, needle, digits)
        if score >= 0:
            matches.append((score, record))
        if len(matches) >= bounded_limit * 4:
            break

    matches.sort(key=lambda item: (item[0], item[1]["symbol"]))
    return [record for _, record in matches[:bounded_limit]]


def score_entry(record: dict[str, Any], needle: str, digits: str) -> int:  # pylint: disable=too-many-return-statements
    symbol = record["symbol"]
    name_lower = record["name"].lower()
    pinyin = record.get("pinyin", "")
    pinyin_initial = record.get("pinyin_initial", "")

    if digits and len(digits) >= 3 and symbol.startswith(digits):
        return 0
    if name_lower.startswith(needle):
        return 1
    if pinyin_initial.startswith(needle) and len(needle) >= 2:
        return 2
    if pinyin.startswith(needle) and len(needle) >= 2:
        return 3
    if needle in name_lower:
        return 4
    if needle in symbol:
        return 5
    if needle in pinyin and len(needle) >= 2:
        return 6
    return -1


@lru_cache(maxsize=1)
def search_index() -> tuple[dict[str, Any], ...]:
    with SEARCH_INDEX_BUILD_LOCK:
        cached = cache_get_json(SEARCH_INDEX_CACHE_KEY)
        if cached:
            return tuple(cached)

        rows: list[dict[str, Any]] = []
        rows.extend(load_a_share_universe())
        rows.extend(load_index_universe())
        rows.extend(load_etf_universe())
        deduped = dedupe_rows(rows)
        stock_count = sum(row["kind"] == "stock" for row in deduped)
        if stock_count >= MINIMUM_COMPLETE_STOCK_COUNT:
            cache_set_json(
                SEARCH_INDEX_CACHE_KEY,
                deduped,
                ttl=SEARCH_INDEX_CACHE_TTL_SECONDS,
            )
            cache_set_json(
                SEARCH_INDEX_STALE_CACHE_KEY,
                deduped,
                ttl=SEARCH_INDEX_STALE_TTL_SECONDS,
            )
        else:
            stale = cache_get_json(SEARCH_INDEX_STALE_CACHE_KEY)
            if stale:
                return tuple(stale)
        return tuple(deduped)


def dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for row in rows:
        key = (row["kind"], row["symbol"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def reset_search_index() -> None:
    search_index.cache_clear()


def load_a_share_universe() -> list[dict[str, Any]]:
    ak = load_akshare()
    rows: list[dict[str, Any]] = []
    try:
        frame = ak.stock_info_a_code_name()
    except Exception:  # pylint: disable=broad-exception-caught
        frame = None
    rows.extend(_normalize_a_share_rows(frame))

    bse_rows = _load_bse_universe(ak)
    if bse_rows:
        rows.extend(bse_rows)
    return rows


def _normalize_a_share_rows(frame: Any) -> list[dict[str, Any]]:
    if frame is None or not hasattr(frame, "to_dict"):
        return []
    rows: list[dict[str, Any]] = []
    for record in frame.to_dict("records"):
        symbol = stringify(record.get("code"))
        name = stringify(record.get("name"))
        if len(symbol) != 6 or not name:
            continue
        rows.append(
            entry(
                kind="stock",
                symbol=symbol,
                name=name,
                exchange=infer_exchange(symbol),
            )
        )
    return rows


def _load_bse_universe(ak: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        bse_frame = ak.stock_info_bj_name_code()
    except Exception:  # pylint: disable=broad-exception-caught
        return rows
    if not hasattr(bse_frame, "to_dict"):
        return rows
    for record in bse_frame.to_dict("records"):
        symbol = stringify(record.get("证券代码") or record.get("code"))
        name = stringify(record.get("证券简称") or record.get("name"))
        if len(symbol) != 6 or not name:
            continue
        rows.append(
            entry(
                kind="stock",
                symbol=symbol,
                name=name,
                exchange="BSE",
            )
        )
    return rows


def load_index_universe() -> list[dict[str, Any]]:
    ak = load_akshare()
    rows: list[dict[str, Any]] = []
    try:
        frame = ak.stock_zh_index_spot_em(symbol="沪深重要指数")
    except Exception:  # pylint: disable=broad-exception-caught
        try:
            frame = ak.stock_zh_index_spot_sina()
        except Exception:  # pylint: disable=broad-exception-caught
            return rows
    if not hasattr(frame, "to_dict"):
        return rows
    for record in frame.to_dict("records"):
        symbol = provider_symbol(record.get("代码"))
        name = stringify(record.get("名称"))
        if len(symbol) != 6 or not name:
            continue
        rows.append(
            entry(
                kind="index",
                symbol=symbol,
                name=name,
                exchange=infer_exchange(symbol),
            )
        )
    return rows


def load_etf_universe() -> list[dict[str, Any]]:
    ak = load_akshare()
    rows: list[dict[str, Any]] = []
    try:
        frame = ak.fund_etf_spot_ths()
    except Exception:  # pylint: disable=broad-exception-caught
        try:
            frame = ak.fund_etf_category_sina(symbol="ETF基金")
        except Exception:  # pylint: disable=broad-exception-caught
            return rows
    if not hasattr(frame, "to_dict"):
        return rows
    for record in frame.to_dict("records"):
        symbol = provider_symbol(record.get("基金代码") or record.get("代码"))
        name = stringify(record.get("基金名称") or record.get("名称"))
        if len(symbol) != 6 or not name:
            continue
        rows.append(
            entry(
                kind="etf",
                symbol=symbol,
                name=name,
                exchange=infer_exchange(symbol),
            )
        )
    return rows


def entry(kind: str, symbol: str, name: str, exchange: str) -> dict[str, Any]:
    pinyin, pinyin_initial = pinyin_for(name)
    return {
        "kind": kind,
        "symbol": symbol,
        "name": name,
        "exchange": exchange,
        "pinyin": pinyin,
        "pinyin_initial": pinyin_initial,
    }


def pinyin_for(name: str) -> tuple[str, str]:
    try:
        from pypinyin import lazy_pinyin, Style  # pylint: disable=import-outside-toplevel
    except ImportError:
        return ("", "")
    full = "".join(lazy_pinyin(name, style=Style.NORMAL)).lower()
    initial = "".join(lazy_pinyin(name, style=Style.FIRST_LETTER)).lower()
    return (full, initial)
