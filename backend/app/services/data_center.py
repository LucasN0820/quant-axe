"""Data Center serving helpers built on top of current provider adapters."""

from __future__ import annotations

import copy
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from typing import Any

from backend.app.services.config import (
    INDEX_CACHE_TTL_SECONDS,
    QUOTE_BATCH_MAX_SYMBOLS,
    QUOTE_CACHE_TTL_SECONDS,
    QUOTE_PROVIDER_MAX_WORKERS,
)
from backend.app.services.data_quality import open_date_set, summarize_issues, validate_daily_bars
from backend.app.services.market_data import (
    get_indexes,
    get_kline,
    get_quote,
    individual_info_map,
    normalize_symbol,
    stock_code_name_rows,
    stringify,
    to_float,
)
from backend.app.services.reference_utils import (
    infer_exchange,
    normalize_provider_date,
    utc_now,
)
from backend.app.services.news_r2 import r2_provider_status
from backend.app.db.migrations import initialize_database
from backend.app.services.storage import (
    cache_get_json,
    cache_set_json,
    postgres_status,
    record_job,
    redis_status,
    save_raw_payload,
    upsert_daily_bars,
    upsert_stock_profile,
    upsert_stock_status,
    upsert_trade_calendar,
)

DATA_JOB_DEFINITIONS = {
    "initialize_storage": "Apply PostgreSQL schema migrations for local Data Center storage",
    "stock_profiles": "Refresh stock profile reference data",
    "tushare_stock_profiles": "Refresh stock profiles from Tushare",
    "trade_calendar": "Refresh exchange trading calendar",
    "daily_bars": "Refresh unadjusted/qfq/hfq daily bars",
    "stock_status": "Refresh ST/suspension/limit status",
    "news": "Refresh hot and stock news",
    "hot_keywords": "Refresh sentiment hot keywords",
    "financials": "Refresh Tushare valuation and quality metrics",
    "quality_daily_bars": "Run daily bar quality checks",
}

RUNTIME_CACHE: dict[str, tuple[float, Any]] = {}


def data_health() -> dict[str, Any]:
    from backend.app.services.scheduler_state import (  # pylint: disable=import-outside-toplevel
        scheduler_status,
    )
    from backend.app.services.tushare_data import (  # pylint: disable=import-outside-toplevel
        tushare_status,
    )

    return {
        "status": "partial",
        "service": "quantdash-data-center",
        "updated_at": utc_now(),
        "providers": [
            {
                "id": "akshare",
                "status": "configured",
                "role": "market/reference/news/financials/announcements",
            },
            r2_provider_status(),
            tushare_status() | {"role": "reference/supplement"},
        ],
        "storage": [
            postgres_status(),
            redis_status(),
            {"id": "parquet_duckdb", "status": "deferred", "note": "PG-only for MVP"},
        ],
        "scheduler": scheduler_status(),
    }


def list_data_jobs() -> dict[str, Any]:
    return {
        "source": "runtime_job_catalog",
        "status": "partial",
        "updated_at": utc_now(),
        "data": [
            {
                "id": job_type,
                "job_type": job_type,
                "description": description,
                "status": "not_scheduled",
                "started_at": None,
                "finished_at": None,
                "error": None,
            }
            for job_type, description in DATA_JOB_DEFINITIONS.items()
        ],
    }


def run_data_job(job_type: str) -> dict[str, Any]:
    if job_type not in DATA_JOB_DEFINITIONS:
        raise ValueError(f"unknown data job type: {job_type}")
    started_at = utc_now()
    try:
        if job_type == "initialize_storage":
            result = initialize_database()
        elif job_type == "stock_profiles":
            result = refresh_stock_profiles()
        elif job_type == "tushare_stock_profiles":
            result = refresh_tushare_stock_profiles()
        elif job_type == "trade_calendar":
            result = refresh_trade_calendar()
        elif job_type == "news":
            result = refresh_hot_news()
        elif job_type == "hot_keywords":
            result = refresh_hot_keywords()
        elif job_type == "financials":
            result = refresh_financials_for_watchlist()
        else:
            result = {
                "status": "not_implemented",
                "reason": "job runner is not implemented yet",
            }
        finished_at = utc_now()
        record_job(job_type, result["status"], started_at=started_at, finished_at=finished_at)
        return {
            "id": f"manual-{job_type}",
            "job_type": job_type,
            "status": result["status"],
            "started_at": started_at,
            "finished_at": finished_at,
            "result": result,
        }
    except Exception as error:  # pylint: disable=broad-exception-caught
        finished_at = utc_now()
        try:
            record_job(
                job_type,
                "failed",
                started_at=started_at,
                finished_at=finished_at,
                error=str(error),
            )
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        return {
            "id": f"manual-{job_type}",
            "job_type": job_type,
            "status": "failed",
            "started_at": started_at,
            "finished_at": finished_at,
            "error": str(error),
        }


def refresh_stock_profiles() -> dict[str, Any]:
    rows = []
    for row in stock_code_name_rows():
        symbol = stringify(row.get("code"))
        name = stringify(row.get("name")) or symbol
        profile = {
            "symbol": symbol,
            "name": name,
            "exchange": infer_exchange(symbol),
            "industry": None,
            "listed_at": None,
            "delisted_at": None,
            "pinyin": None,
            "source": "akshare.stock_info_a_code_name",
            "updated_at": utc_now(),
        }
        upsert_stock_profile(profile)
        rows.append(profile)
    save_raw_payload("akshare", "stock_info_a_code_name", rows)
    return {"status": "ready", "rows": len(rows)}


def refresh_tushare_stock_profiles() -> dict[str, Any]:
    from backend.app.services.tushare_data import (  # pylint: disable=import-outside-toplevel
        fetch_tushare_stock_profiles,
    )

    rows = fetch_tushare_stock_profiles()
    for profile in rows:
        upsert_stock_profile(profile)
    save_raw_payload("tushare", "stock_basic", rows)
    return {"status": "ready", "rows": len(rows)}


def refresh_trade_calendar() -> dict[str, Any]:
    payload = trading_days("1990-01-01", date.today().isoformat())
    upsert_trade_calendar(payload["data"])
    save_raw_payload("akshare", "tool_trade_date_hist_sina", payload["data"])
    return {"status": "ready", "rows": len(payload["data"])}


def refresh_hot_news() -> dict[str, Any]:
    from backend.app.services.news_r2 import refresh_snapshot  # pylint: disable=import-outside-toplevel

    snapshot = refresh_snapshot(force=True)
    return {
        "status": "ready",
        "snapshot_key": snapshot.key,
        "snapshot_etag": snapshot.etag,
        "stale": snapshot.stale,
    }


def refresh_hot_keywords() -> dict[str, Any]:
    from backend.app.services.sentiment_data import (  # pylint: disable=import-outside-toplevel
        get_hot_keywords,
    )

    payload = get_hot_keywords(limit=50)
    return {"status": payload.get("status", "unknown"), "rows": len(payload.get("data", []))}


def refresh_financials_for_watchlist() -> dict[str, Any]:
    from backend.app.services.config import (  # pylint: disable=import-outside-toplevel
        DAILY_REFRESH_WATCHLIST,
    )
    from backend.app.services.financials_data import (  # pylint: disable=import-outside-toplevel
        get_financial_metrics,
    )

    refreshed = 0
    failed: list[str] = []
    for symbol in DAILY_REFRESH_WATCHLIST:
        try:
            payload = get_financial_metrics(symbol)
            if payload.get("status") == "ready":
                refreshed += 1
        except Exception as error:  # pylint: disable=broad-exception-caught
            failed.append(f"{symbol}:{error}")
    return {
        "status": "ready" if refreshed > 0 else "empty",
        "refreshed": refreshed,
        "failed": failed,
    }


def get_served_kline(symbol: str, ktype: str = "daily", adjust: str = "none") -> dict[str, Any]:
    clean = normalize_symbol(symbol)
    cache_key = f"kline:{clean}:{ktype}:{adjust}"
    cached = cache_get_json(cache_key)
    if cached is not None:
        cached["cache"] = "redis"
        return cached

    payload = get_kline(clean, ktype, adjust=adjust)
    if ktype == "daily":
        try:
            upsert_daily_bars(clean, adjust, payload["source"], payload["data"])
            save_raw_payload(payload["source"], f"daily_bars_{adjust}", payload["data"], clean)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
    cache_set_json(cache_key, payload)
    return payload


def get_served_quote(symbol: str) -> dict[str, Any]:
    clean = normalize_symbol(symbol)
    cache_key = f"quote:{clean}"
    cached = served_cache_get(cache_key)
    if cached is not None:
        return cached

    payload = get_quote(clean)
    served_cache_set(cache_key, payload, ttl=QUOTE_CACHE_TTL_SECONDS)
    return payload


def get_served_quotes(symbols_text: str) -> dict[str, Any]:
    symbols = normalize_symbol_list(symbols_text)
    if len(symbols) > QUOTE_BATCH_MAX_SYMBOLS:
        raise ValueError(f"too many symbols, max is {QUOTE_BATCH_MAX_SYMBOLS}")

    quotes: list[dict[str, Any]] = []
    failed: list[dict[str, str]] = []
    hits = 0
    misses: list[str] = []
    for symbol in symbols:
        cached = served_cache_get(f"quote:{symbol}")
        if cached is None:
            misses.append(symbol)
            continue
        quotes.append(cached)
        hits += 1

    if misses:
        max_workers = max(1, min(QUOTE_PROVIDER_MAX_WORKERS, len(misses)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(get_quote, symbol): symbol for symbol in misses}
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    quote = future.result()
                    served_cache_set(f"quote:{symbol}", quote, ttl=QUOTE_CACHE_TTL_SECONDS)
                    quotes.append(quote)
                except Exception as error:  # pylint: disable=broad-exception-caught
                    failed.append({"symbol": symbol, "error": str(error)})

    quotes.sort(key=lambda row: symbols.index(row["symbol"]))
    status = quote_batch_status(quotes, failed)
    return {
        "source": "quote_batch",
        "status": status,
        "updated_at": utc_now(),
        "cache": {"hits": hits, "misses": len(misses)},
        "data": quotes,
        "failed": failed,
    }


def get_served_indexes() -> dict[str, Any]:
    cache_key = "market:indexes"
    cached = served_cache_get(cache_key)
    if cached is not None:
        return cached

    payload = get_indexes()
    served_cache_set(cache_key, payload, ttl=INDEX_CACHE_TTL_SECONDS)
    return payload


def get_market_snapshot(symbols_text: str) -> dict[str, Any]:
    quotes = get_served_quotes(symbols_text) if symbols_text.strip() else empty_quotes_payload()
    try:
        indexes = get_served_indexes()
    except Exception as error:  # pylint: disable=broad-exception-caught
        indexes = unavailable_indexes_payload(error)
    return {
        "source": "market_snapshot",
        "status": snapshot_status(quotes, indexes),
        "updated_at": utc_now(),
        "quotes": quotes,
        "indexes": indexes,
    }


def normalize_symbol_list(symbols_text: str) -> list[str]:
    symbols = []
    seen = set()
    for item in symbols_text.split(","):
        text = item.strip()
        if not text:
            continue
        symbol = normalize_symbol(text)
        if symbol in seen:
            continue
        seen.add(symbol)
        symbols.append(symbol)
    return symbols


def empty_quotes_payload() -> dict[str, Any]:
    return {
        "source": "quote_batch",
        "status": "empty",
        "updated_at": utc_now(),
        "cache": {"hits": 0, "misses": 0},
        "data": [],
        "failed": [],
    }


def quote_batch_status(quotes: list[dict[str, Any]], failed: list[dict[str, str]]) -> str:
    if quotes and not failed:
        return "ready"
    if quotes:
        return "partial"
    if failed:
        return "error"
    return "empty"


def snapshot_status(quotes: dict[str, Any], indexes: dict[str, Any]) -> str:
    if quotes.get("status") == "error" or indexes.get("status") == "unavailable":
        return "partial"
    return "ready"


def unavailable_indexes_payload(error: Exception) -> dict[str, Any]:
    return {
        "source": "akshare.stock_zh_index_spot_em",
        "status": "unavailable",
        "message": str(error),
        "updated_at": utc_now(),
        "data": [],
    }


def served_cache_get(key: str) -> Any | None:
    cached = cache_get_json(key)
    if cached is not None:
        cached["cache"] = "redis"
        return cached

    item = RUNTIME_CACHE.get(key)
    if item is None:
        return None
    expires_at, value = item
    if expires_at <= time.monotonic():
        RUNTIME_CACHE.pop(key, None)
        return None
    payload = copy.deepcopy(value)
    payload["cache"] = "memory"
    return payload


def served_cache_set(key: str, value: Any, ttl: int) -> None:
    RUNTIME_CACHE[key] = (time.monotonic() + ttl, copy.deepcopy(value))
    cache_set_json(key, value, ttl=ttl)


def persist_stock_status(payload: dict[str, Any]) -> None:
    try:
        upsert_stock_status(payload)
    except Exception:  # pylint: disable=broad-exception-caught
        pass


def persist_stock_profile(profile: dict[str, Any]) -> None:
    try:
        upsert_stock_profile(profile)
    except Exception:  # pylint: disable=broad-exception-caught
        pass


def persist_trade_calendar(payload: dict[str, Any]) -> None:
    try:
        upsert_trade_calendar(payload["data"])
    except Exception:  # pylint: disable=broad-exception-caught
        pass


def get_announcements(symbol: str, limit: int = 30) -> dict[str, Any]:
    from backend.app.services.storage import insert_news_items  # pylint: disable=import-outside-toplevel
    from backend.app.services.tushare_data import (  # pylint: disable=import-outside-toplevel
        fetch_tushare_announcements,
    )

    clean = normalize_symbol(symbol)
    try:
        payload = fetch_tushare_announcements(clean, limit)
    except Exception as error:  # pylint: disable=broad-exception-caught
        return {
            "symbol": clean,
            "source": "akshare.stock_notice_report",
            "status": "unavailable",
            "message": str(error),
            "data": [],
        }
    try:
        insert_news_items(payload["data"], "announcement")
        save_raw_payload("akshare", "anns", payload["data"], clean)
    except Exception:  # pylint: disable=broad-exception-caught
        pass
    return payload


def not_configured_job(job_type: str) -> dict[str, Any]:
    return {
        "id": f"manual-{job_type}",
        "job_type": job_type,
        "status": "not_configured",
        "started_at": None,
        "finished_at": None,
        "error": "persistent scheduler/storage is not configured yet",
    }


def stock_profile(symbol: str) -> dict[str, Any]:
    clean = normalize_symbol(symbol)
    info = individual_info_map(clean)
    name = stringify(info.get("股票简称")) or stock_name(clean) or clean
    listed_at = normalize_provider_date(info.get("上市时间"))
    payload = {
        "symbol": clean,
        "name": name,
        "exchange": infer_exchange(clean),
        "industry": stringify(info.get("行业")),
        "listed_at": listed_at,
        "delisted_at": None,
        "pinyin": None,
        "source": "akshare.stock_individual_info_em",
        "updated_at": utc_now(),
    }
    persist_stock_profile(payload)
    return payload


def search_stock_profiles(query: str, limit: int = 20) -> dict[str, Any]:
    text = query.strip().lower()
    rows = []
    if text:
        for row in stock_code_name_rows():
            symbol = stringify(row.get("code"))
            name = stringify(row.get("name"))
            if text in symbol.lower() or text in name.lower():
                rows.append(
                    {
                        "symbol": symbol,
                        "name": name,
                        "exchange": infer_exchange(symbol),
                        "industry": None,
                        "listed_at": None,
                        "delisted_at": None,
                        "pinyin": None,
                        "source": "akshare.stock_info_a_code_name",
                        "updated_at": utc_now(),
                    }
                )
            if len(rows) >= limit:
                break

    return {
        "source": "akshare.stock_info_a_code_name",
        "status": "ready",
        "query": query,
        "updated_at": utc_now(),
        "data": rows,
    }


def trading_days(start: str | None, end: str | None, exchange: str = "SSE") -> dict[str, Any]:
    end_date = date.fromisoformat(end) if end else date.today()
    start_date = date.fromisoformat(start) if start else end_date - timedelta(days=30)
    if start_date > end_date:
        raise ValueError("start must be before or equal to end")

    ak = load_akshare()
    frame = ak.tool_trade_date_hist_sina()
    open_dates = {
        normalize_provider_date(row.get("trade_date"))
        for row in frame.to_dict("records")
        if normalize_provider_date(row.get("trade_date"))
    }

    rows = []
    current = start_date
    while current <= end_date:
        rows.append(
            {
                "date": current.isoformat(),
                "is_open": current.isoformat() in open_dates,
                "exchange": exchange,
                "source": "akshare.tool_trade_date_hist_sina",
                "updated_at": utc_now(),
            }
        )
        current += timedelta(days=1)

    payload = {
        "source": "akshare.tool_trade_date_hist_sina",
        "status": "ready",
        "updated_at": utc_now(),
        "data": rows,
    }
    persist_trade_calendar(payload)
    return payload


def stock_status(symbol: str, target_date: str | None) -> dict[str, Any]:
    clean = normalize_symbol(symbol)
    query_date = date.fromisoformat(target_date) if target_date else latest_daily_bar_date(clean)
    profile = stock_profile(clean)
    daily = get_served_kline(clean, "daily", adjust="none")
    bars = {row["date"]: row for row in daily["data"]}
    prev_bar = previous_bar(daily["data"], query_date.isoformat())
    daily_bar = bars.get(query_date.isoformat())
    up_limit, down_limit = calculate_limit_prices(clean, prev_bar, profile["name"])
    is_suspended = daily_bar is None
    close = to_float(daily_bar.get("close")) if daily_bar else None

    payload = {
        "symbol": clean,
        "date": query_date.isoformat(),
        "source": daily.get("source"),
        "updated_at": utc_now(),
        "data": {
            "is_st": is_st_name(profile["name"]),
            "is_suspended": is_suspended,
            "up_limit": up_limit,
            "down_limit": down_limit,
            "is_limit_up": close is not None and up_limit is not None and close >= up_limit,
            "is_limit_down": close is not None and down_limit is not None and close <= down_limit,
            "status_scope": "current_st_name_and_daily_bar_presence",
        },
    }
    persist_stock_status(payload)
    return payload


def quality_daily_bars(symbol: str, adjust: str = "none") -> dict[str, Any]:
    clean = normalize_symbol(symbol)
    daily = get_served_kline(clean, "daily", adjust=adjust)
    rows = daily["data"]
    if rows:
        calendar = trading_days(rows[0]["date"], rows[-1]["date"])
        open_dates = open_date_set(calendar["data"])
    else:
        open_dates = set()
    issues = validate_daily_bars(rows, open_dates=open_dates)
    return {
        "symbol": clean,
        "source": daily.get("source"),
        "status": "pass" if not issues else "fail",
        "adjust": adjust,
        "updated_at": utc_now(),
        "data": summarize_issues(issues),
    }


def previous_bar(rows: list[dict[str, Any]], target_date: str) -> dict[str, Any] | None:
    previous = None
    for row in rows:
        row_date = stringify(row.get("date"))
        if row_date >= target_date:
            return previous
        previous = row
    return previous


def latest_daily_bar_date(symbol: str) -> date:
    daily = get_served_kline(symbol, "daily", adjust="none")
    if not daily["data"]:
        return date.today()
    return date.fromisoformat(daily["data"][-1]["date"])


def calculate_limit_prices(
    symbol: str,
    prev_bar: dict[str, Any] | None,
    name: str,
) -> tuple[float | None, float | None]:
    previous_close = to_float(prev_bar.get("close")) if prev_bar else None
    if previous_close is None:
        return None, None
    ratio = limit_ratio(symbol, name)
    return round(previous_close * (1 + ratio), 2), round(previous_close * (1 - ratio), 2)


def limit_ratio(symbol: str, name: str) -> float:
    if is_st_name(name):
        return 0.05
    if symbol.startswith(("300", "301", "688")):
        return 0.20
    return 0.10


def is_st_name(name: str) -> bool:
    normalized = name.upper()
    return "ST" in normalized


def stock_name(symbol: str) -> str:
    for row in stock_code_name_rows():
        if stringify(row.get("code")) == symbol:
            return stringify(row.get("name"))
    return ""

def load_akshare():
    import akshare as ak  # pylint: disable=import-outside-toplevel

    return ak
