"""PostgreSQL persistence and Redis cache helpers for Data Center."""

from __future__ import annotations

import json
from collections.abc import Iterable
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from backend.app.services.config import CACHE_TTL_SECONDS, POSTGRES_DSN, REDIS_URL


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS raw_payloads (
      id BIGSERIAL PRIMARY KEY,
      provider TEXT NOT NULL,
      dataset TEXT NOT NULL,
      symbol TEXT,
      payload JSONB NOT NULL,
      fetched_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS stock_profiles (
      symbol TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      exchange TEXT NOT NULL,
      industry TEXT,
      listed_at DATE,
      delisted_at DATE,
      pinyin TEXT,
      source TEXT NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS trade_calendar (
      exchange TEXT NOT NULL,
      date DATE NOT NULL,
      is_open BOOLEAN NOT NULL,
      source TEXT NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL,
      PRIMARY KEY (exchange, date)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_bars (
      symbol TEXT NOT NULL,
      date DATE NOT NULL,
      open DOUBLE PRECISION,
      high DOUBLE PRECISION,
      low DOUBLE PRECISION,
      close DOUBLE PRECISION,
      volume BIGINT,
      turnover DOUBLE PRECISION,
      amplitude DOUBLE PRECISION,
      change_rate DOUBLE PRECISION,
      change_amount DOUBLE PRECISION,
      turnover_rate DOUBLE PRECISION,
      adjust_type TEXT NOT NULL,
      source TEXT NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL,
      PRIMARY KEY (symbol, date, adjust_type)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS stock_status (
      symbol TEXT NOT NULL,
      date DATE NOT NULL,
      is_st BOOLEAN NOT NULL,
      is_suspended BOOLEAN NOT NULL,
      source TEXT NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL,
      PRIMARY KEY (symbol, date)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS limit_prices (
      symbol TEXT NOT NULL,
      date DATE NOT NULL,
      up_limit DOUBLE PRECISION,
      down_limit DOUBLE PRECISION,
      source TEXT NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL,
      PRIMARY KEY (symbol, date)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS financial_metrics (
      symbol TEXT NOT NULL,
      report_period TEXT NOT NULL,
      pe_ttm DOUBLE PRECISION,
      pb DOUBLE PRECISION,
      roe DOUBLE PRECISION,
      gross_margin DOUBLE PRECISION,
      source TEXT NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL,
      PRIMARY KEY (symbol, report_period, source)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS hot_news_items (
      id BIGSERIAL PRIMARY KEY,
      source_id TEXT NOT NULL,
      source_name TEXT NOT NULL,
      rank INTEGER,
      title TEXT NOT NULL,
      url TEXT,
      updated_at TIMESTAMPTZ,
      captured_at TIMESTAMPTZ NOT NULL,
      UNIQUE (source_id, title, captured_at)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS news_items (
      id BIGSERIAL PRIMARY KEY,
      symbol TEXT,
      title TEXT NOT NULL,
      summary TEXT,
      source TEXT NOT NULL,
      url TEXT,
      published_at TIMESTAMPTZ,
      type TEXT NOT NULL,
      captured_at TIMESTAMPTZ NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS hot_keywords (
      id BIGSERIAL PRIMARY KEY,
      word TEXT NOT NULL,
      heat DOUBLE PRECISION,
      sources JSONB NOT NULL,
      captured_at TIMESTAMPTZ NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS data_jobs (
      id BIGSERIAL PRIMARY KEY,
      job_type TEXT NOT NULL,
      status TEXT NOT NULL,
      started_at TIMESTAMPTZ,
      finished_at TIMESTAMPTZ,
      error TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS universes (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      base TEXT NOT NULL,
      filters JSONB NOT NULL,
      created_at TIMESTAMPTZ NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS universe_members (
      universe_id TEXT NOT NULL,
      date DATE NOT NULL,
      symbol TEXT NOT NULL,
      name TEXT NOT NULL,
      included BOOLEAN NOT NULL,
      excluded_reason TEXT,
      can_buy BOOLEAN NOT NULL,
      can_sell BOOLEAN NOT NULL,
      flags JSONB NOT NULL,
      created_at TIMESTAMPTZ NOT NULL,
      PRIMARY KEY (universe_id, date, symbol)
    )
    """,
]


@contextmanager
def postgres_connection():
    import psycopg  # pylint: disable=import-outside-toplevel

    connection: Any = psycopg.connect(POSTGRES_DSN)
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


def ensure_schema() -> dict[str, Any]:
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            for statement in SCHEMA_STATEMENTS:
                cursor.execute(statement)
    return {"status": "ready", "tables": len(SCHEMA_STATEMENTS)}


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
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO universes (id, name, base, filters, created_at, updated_at)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                  name = EXCLUDED.name,
                  base = EXCLUDED.base,
                  filters = EXCLUDED.filters,
                  updated_at = EXCLUDED.updated_at
                """,
                (
                    universe["id"],
                    universe["name"],
                    universe["base"],
                    json.dumps(universe.get("filters") or [], ensure_ascii=False),
                    universe["created_at"],
                    universe["updated_at"],
                ),
            )


def fetch_universes() -> list[dict[str, Any]]:
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, base, filters, created_at, updated_at
                FROM universes
                ORDER BY created_at, id
                """
            )
            columns = [desc[0] for desc in cursor.description]
            return [
                decode_json_columns(dict(zip(columns, row)), {"filters"})
                for row in cursor.fetchall()
            ]


def fetch_universe(universe_id: str) -> dict[str, Any] | None:
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, base, filters, created_at, updated_at
                FROM universes
                WHERE id = %s
                """,
                (universe_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            columns = [desc[0] for desc in cursor.description]
            return decode_json_columns(dict(zip(columns, row)), {"filters"})


def delete_universe(universe_id: str) -> bool:
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM universe_members WHERE universe_id = %s", (universe_id,))
            cursor.execute("DELETE FROM universes WHERE id = %s", (universe_id,))
            return bool(cursor.rowcount)


def fetch_stock_profiles_as_of(target_date: str) -> list[dict[str, Any]]:
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT symbol, name, exchange, industry, listed_at, delisted_at, pinyin,
                       source, updated_at
                FROM stock_profiles
                WHERE (listed_at IS NULL OR listed_at <= %s)
                  AND (delisted_at IS NULL OR delisted_at > %s)
                ORDER BY symbol
                """,
                (target_date, target_date),
            )
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetch_daily_bars_for_date(
    target_date: str,
    symbols: Iterable[str],
) -> dict[str, dict[str, Any]]:
    symbol_list = tuple(symbols)
    if not symbol_list:
        return {}
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT symbol, date, open, high, low, close, volume, turnover,
                       amplitude, change_rate, change_amount, turnover_rate,
                       adjust_type, source, updated_at
                FROM daily_bars
                WHERE date = %s AND adjust_type = 'none' AND symbol = ANY(%s)
                """,
                (target_date, list(symbol_list)),
            )
            columns = [desc[0] for desc in cursor.description]
            return {row[0]: dict(zip(columns, row)) for row in cursor.fetchall()}


def fetch_stock_status_for_date(
    target_date: str,
    symbols: Iterable[str],
) -> dict[str, dict[str, Any]]:
    symbol_list = tuple(symbols)
    if not symbol_list:
        return {}
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT symbol, date, is_st, is_suspended, source, updated_at
                FROM stock_status
                WHERE date = %s AND symbol = ANY(%s)
                """,
                (target_date, list(symbol_list)),
            )
            columns = [desc[0] for desc in cursor.description]
            return {row[0]: dict(zip(columns, row)) for row in cursor.fetchall()}


def fetch_limit_prices_for_date(
    target_date: str,
    symbols: Iterable[str],
) -> dict[str, dict[str, Any]]:
    symbol_list = tuple(symbols)
    if not symbol_list:
        return {}
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT symbol, date, up_limit, down_limit, source, updated_at
                FROM limit_prices
                WHERE date = %s AND symbol = ANY(%s)
                """,
                (target_date, list(symbol_list)),
            )
            columns = [desc[0] for desc in cursor.description]
            return {row[0]: dict(zip(columns, row)) for row in cursor.fetchall()}


def upsert_universe_members(
    universe_id: str,
    target_date: str,
    rows: Iterable[dict[str, Any]],
) -> int:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    count = 0
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            for row in rows:
                cursor.execute(
                    """
                    INSERT INTO universe_members
                      (universe_id, date, symbol, name, included, excluded_reason,
                       can_buy, can_sell, flags, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                    ON CONFLICT (universe_id, date, symbol) DO UPDATE SET
                      name = EXCLUDED.name,
                      included = EXCLUDED.included,
                      excluded_reason = EXCLUDED.excluded_reason,
                      can_buy = EXCLUDED.can_buy,
                      can_sell = EXCLUDED.can_sell,
                      flags = EXCLUDED.flags,
                      created_at = EXCLUDED.created_at
                    """,
                    (
                        universe_id,
                        target_date,
                        row["symbol"],
                        row["name"],
                        row["included"],
                        row.get("excluded_reason"),
                        row.get("can_buy", True),
                        row.get("can_sell", True),
                        json.dumps(row.get("flags") or [], ensure_ascii=False),
                        now,
                    ),
                )
                count += 1
    return count


def fetch_universe_members(universe_id: str, target_date: str) -> list[dict[str, Any]]:
    with postgres_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, universe_id, symbol, name, included, excluded_reason,
                       can_buy, can_sell, flags, created_at
                FROM universe_members
                WHERE universe_id = %s AND date = %s
                ORDER BY included DESC, symbol
                """,
                (universe_id, target_date),
            )
            columns = [desc[0] for desc in cursor.description]
            return [
                decode_json_columns(dict(zip(columns, row)), {"flags"})
                for row in cursor.fetchall()
            ]


def decode_json_columns(row: dict[str, Any], keys: set[str]) -> dict[str, Any]:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str):
            row[key] = json.loads(value)
    return row


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
