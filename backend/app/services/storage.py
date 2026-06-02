"""PostgreSQL persistence and Redis cache helpers for Data Center."""

from __future__ import annotations

import json
from collections.abc import Iterable
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from backend.app.db.engine import engine
from backend.app.db.repositories import universes as universe_repository
from backend.app.services.config import CACHE_TTL_SECONDS, POSTGRES_DSN, REDIS_URL


@contextmanager
def postgres_connection():
    """Provide a pooled raw DBAPI connection during incremental migration."""

    connection: Any = engine.raw_connection()
    try:
        yield connection
        connection.commit()  # pylint: disable=no-member
    except Exception:
        connection.rollback()  # pylint: disable=no-member
        raise
    finally:
        connection.close()  # pylint: disable=no-member


def postgres_status() -> dict[str, Any]:
    try:
        with postgres_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return {"id": "postgresql", "status": "ready", "dsn": redact_dsn(POSTGRES_DSN)}
    except Exception as error:  # pylint: disable=broad-exception-caught
        return {
            "id": "postgresql",
            "status": "unavailable",
            "dsn": redact_dsn(POSTGRES_DSN),
            "error": str(error),
        }


def redis_status() -> dict[str, Any]:
    try:
        client = redis_client()
        client.ping()
        return {"id": "redis", "status": "ready", "url": redact_dsn(REDIS_URL)}
    except Exception as error:  # pylint: disable=broad-exception-caught
        return {
            "id": "redis",
            "status": "unavailable",
            "url": redact_dsn(REDIS_URL),
            "error": str(error),
        }


def record_job(
    job_type: str,
    status: str,
    *,
    started_at: str | None = None,
    finished_at: str | None = None,
    error: str | None = None,
) -> None:
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO data_jobs (job_type, status, started_at, finished_at, error)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (job_type, status, started_at, finished_at, error),
            )


def save_raw_payload(provider: str, dataset: str, payload: Any, symbol: str | None = None) -> None:
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO raw_payloads (provider, dataset, symbol, payload)
                VALUES (%s, %s, %s, %s::jsonb)
                """,
                (provider, dataset, symbol, json.dumps(payload, ensure_ascii=False, default=str)),
            )


def upsert_stock_profile(profile: dict[str, Any]) -> None:
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO stock_profiles
                  (symbol, name, exchange, industry, listed_at, delisted_at,
                   pinyin, source, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol) DO UPDATE SET
                  name = EXCLUDED.name,
                  exchange = EXCLUDED.exchange,
                  industry = EXCLUDED.industry,
                  listed_at = EXCLUDED.listed_at,
                  delisted_at = EXCLUDED.delisted_at,
                  pinyin = EXCLUDED.pinyin,
                  source = EXCLUDED.source,
                  updated_at = EXCLUDED.updated_at
                """,
                (
                    profile["symbol"],
                    profile["name"],
                    profile["exchange"],
                    profile.get("industry"),
                    profile.get("listed_at"),
                    profile.get("delisted_at"),
                    profile.get("pinyin"),
                    profile["source"],
                    profile["updated_at"],
                ),
            )


def upsert_trade_calendar(rows: Iterable[dict[str, Any]]) -> None:
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            for row in rows:
                cursor.execute(
                    """
                    INSERT INTO trade_calendar (exchange, date, is_open, source, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (exchange, date) DO UPDATE SET
                      is_open = EXCLUDED.is_open,
                      source = EXCLUDED.source,
                      updated_at = EXCLUDED.updated_at
                    """,
                    (
                        row["exchange"],
                        row["date"],
                        row["is_open"],
                        row["source"],
                        row["updated_at"],
                    ),
                )


def upsert_daily_bars(
    symbol: str,
    adjust_type: str,
    source: str,
    rows: Iterable[dict[str, Any]],
) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            for row in rows:
                cursor.execute(
                    """
                    INSERT INTO daily_bars
                      (symbol, date, open, high, low, close, volume, turnover, amplitude,
                       change_rate, change_amount, turnover_rate, adjust_type, source, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, date, adjust_type) DO UPDATE SET
                      open = EXCLUDED.open,
                      high = EXCLUDED.high,
                      low = EXCLUDED.low,
                      close = EXCLUDED.close,
                      volume = EXCLUDED.volume,
                      turnover = EXCLUDED.turnover,
                      amplitude = EXCLUDED.amplitude,
                      change_rate = EXCLUDED.change_rate,
                      change_amount = EXCLUDED.change_amount,
                      turnover_rate = EXCLUDED.turnover_rate,
                      source = EXCLUDED.source,
                      updated_at = EXCLUDED.updated_at
                    """,
                    (
                        symbol,
                        row["date"],
                        row.get("open"),
                        row.get("high"),
                        row.get("low"),
                        row.get("close"),
                        row.get("volume"),
                        row.get("turnover"),
                        row.get("amplitude"),
                        row.get("change_rate"),
                        row.get("change_amount"),
                        row.get("turnover_rate"),
                        adjust_type,
                        source,
                        now,
                    ),
                )


def upsert_stock_status(payload: dict[str, Any]) -> None:
    data = payload["data"]
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO stock_status (symbol, date, is_st, is_suspended, source, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, date) DO UPDATE SET
                  is_st = EXCLUDED.is_st,
                  is_suspended = EXCLUDED.is_suspended,
                  source = EXCLUDED.source,
                  updated_at = EXCLUDED.updated_at
                """,
                (
                    payload["symbol"],
                    payload["date"],
                    data["is_st"],
                    data["is_suspended"],
                    payload["source"],
                    payload["updated_at"],
                ),
            )
            cursor.execute(
                """
                INSERT INTO limit_prices (symbol, date, up_limit, down_limit, source, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, date) DO UPDATE SET
                  up_limit = EXCLUDED.up_limit,
                  down_limit = EXCLUDED.down_limit,
                  source = EXCLUDED.source,
                  updated_at = EXCLUDED.updated_at
                """,
                (
                    payload["symbol"],
                    payload["date"],
                    data["up_limit"],
                    data["down_limit"],
                    payload["source"],
                    payload["updated_at"],
                ),
            )


def insert_hot_news_items(rows: Iterable[dict[str, Any]]) -> None:
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            for row in rows:
                cursor.execute(
                    """
                    INSERT INTO hot_news_items
                      (source_id, source_name, rank, title, url, updated_at, captured_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_id, title, captured_at) DO NOTHING
                    """,
                    (
                        row.get("source_id"),
                        row.get("source_name") or row.get("source"),
                        row.get("rank"),
                        row.get("title"),
                        row.get("url"),
                        row.get("updated_at") or None,
                        row.get("captured_at"),
                    ),
                )


def upsert_financial_metrics(rows: Iterable[dict[str, Any]]) -> None:
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            for row in rows:
                cursor.execute(
                    """
                    INSERT INTO financial_metrics
                      (symbol, report_period, pe_ttm, pb, roe, gross_margin,
                       source, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, report_period, source) DO UPDATE SET
                      pe_ttm = EXCLUDED.pe_ttm,
                      pb = EXCLUDED.pb,
                      roe = EXCLUDED.roe,
                      gross_margin = EXCLUDED.gross_margin,
                      updated_at = EXCLUDED.updated_at
                    """,
                    (
                        row.get("symbol"),
                        row.get("report_period"),
                        row.get("pe_ttm"),
                        row.get("pb"),
                        row.get("roe"),
                        row.get("gross_margin"),
                        row.get("source"),
                        row.get("updated_at"),
                    ),
                )


def fetch_latest_financial_metrics(symbol: str) -> list[dict[str, Any]]:
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT symbol, report_period, pe_ttm, pb, roe, gross_margin, source, updated_at
                FROM financial_metrics
                WHERE symbol = %s
                ORDER BY report_period DESC, updated_at DESC
                LIMIT 8
                """,
                (symbol,),
            )
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


def insert_hot_keywords(rows: Iterable[dict[str, Any]]) -> None:
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            for row in rows:
                cursor.execute(
                    """
                    INSERT INTO hot_keywords (word, heat, sources, captured_at)
                    VALUES (%s, %s, %s::jsonb, %s)
                    """,
                    (
                        row.get("word"),
                        row.get("heat"),
                        json.dumps(row.get("sources") or [], ensure_ascii=False),
                        row.get("captured_at"),
                    ),
                )


def insert_news_items(rows: Iterable[dict[str, Any]], news_type: str) -> None:
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            for row in rows:
                cursor.execute(
                    """
                    INSERT INTO news_items
                      (symbol, title, summary, source, url, published_at, type, captured_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        row.get("symbol"),
                        row.get("title"),
                        row.get("summary"),
                        row.get("source"),
                        row.get("url"),
                        row.get("published_at") or None,
                        news_type,
                        row.get("captured_at"),
                    ),
                )


def upsert_universe(universe: dict[str, Any]) -> None:
    universe_repository.upsert_universe(universe)


def fetch_universes() -> list[dict[str, Any]]:
    return universe_repository.fetch_universes()


def fetch_universe(universe_id: str) -> dict[str, Any] | None:
    return universe_repository.fetch_universe(universe_id)


def delete_universe(universe_id: str) -> bool:
    return universe_repository.delete_universe(universe_id)


def fetch_stock_profiles_as_of(target_date: str) -> list[dict[str, Any]]:
    return universe_repository.fetch_stock_profiles_as_of(target_date)


def fetch_daily_bars_for_date(
    target_date: str,
    symbols: Iterable[str],
) -> dict[str, dict[str, Any]]:
    return universe_repository.fetch_daily_bars_for_date(target_date, symbols)


def fetch_stock_status_for_date(
    target_date: str,
    symbols: Iterable[str],
) -> dict[str, dict[str, Any]]:
    return universe_repository.fetch_stock_status_for_date(target_date, symbols)


def fetch_limit_prices_for_date(
    target_date: str,
    symbols: Iterable[str],
) -> dict[str, dict[str, Any]]:
    return universe_repository.fetch_limit_prices_for_date(target_date, symbols)


def upsert_universe_members(
    universe_id: str,
    target_date: str,
    rows: Iterable[dict[str, Any]],
) -> int:
    return universe_repository.upsert_universe_members(universe_id, target_date, rows)


def fetch_universe_members(universe_id: str, target_date: str) -> list[dict[str, Any]]:
    return universe_repository.fetch_universe_members(universe_id, target_date)


def cache_get_json(key: str) -> Any | None:
    try:
        value = redis_client().get(key)
    except Exception:  # pylint: disable=broad-exception-caught
        return None
    if value is None:
        return None
    return json.loads(value)


def cache_set_json(key: str, value: Any, ttl: int = CACHE_TTL_SECONDS) -> None:
    try:
        redis_client().setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
    except Exception:  # pylint: disable=broad-exception-caught
        pass


def redis_client():
    import redis  # pylint: disable=import-outside-toplevel

    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def redact_dsn(value: str) -> str:
    if "@" not in value or "://" not in value:
        return value
    scheme, rest = value.split("://", 1)
    return f"{scheme}://***@{rest.split('@', 1)[1]}"
