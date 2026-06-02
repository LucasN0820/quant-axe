"""SQLAlchemy repository for Universe Center persistence."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from backend.app.db.engine import session_scope
from backend.app.db.models import (
    DailyBar,
    LimitPrice,
    StockProfile,
    StockStatus,
    Universe,
    UniverseMember,
)


def _date(value: str) -> date:
    return date.fromisoformat(value)


def _datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def upsert_universe(universe: dict[str, Any]) -> None:
    values = {
        **universe,
        "filters": universe.get("filters") or [],
        "created_at": _datetime(universe["created_at"]),
        "updated_at": _datetime(universe["updated_at"]),
    }
    statement = insert(Universe).values(values)
    statement = statement.on_conflict_do_update(
        index_elements=[Universe.id],
        set_={
            "name": statement.excluded.name,
            "base": statement.excluded.base,
            "filters": statement.excluded.filters,
            "updated_at": statement.excluded.updated_at,
        },
    )
    with session_scope() as session:
        session.execute(statement)


def fetch_universes() -> list[dict[str, Any]]:
    statement = select(
        Universe.id,
        Universe.name,
        Universe.base,
        Universe.filters,
        Universe.created_at,
        Universe.updated_at,
    ).order_by(Universe.created_at, Universe.id)
    with session_scope() as session:
        return [dict(row) for row in session.execute(statement).mappings()]


def fetch_universe(universe_id: str) -> dict[str, Any] | None:
    statement = select(
        Universe.id,
        Universe.name,
        Universe.base,
        Universe.filters,
        Universe.created_at,
        Universe.updated_at,
    ).where(Universe.id == universe_id)
    with session_scope() as session:
        row = session.execute(statement).mappings().one_or_none()
        return dict(row) if row is not None else None


def delete_universe(universe_id: str) -> bool:
    with session_scope() as session:
        session.execute(delete(UniverseMember).where(UniverseMember.universe_id == universe_id))
        result = session.execute(delete(Universe).where(Universe.id == universe_id))
        return bool(result.rowcount)


def fetch_stock_profiles_as_of(target_date: str) -> list[dict[str, Any]]:
    target = _date(target_date)
    statement = (
        select(
            StockProfile.symbol,
            StockProfile.name,
            StockProfile.exchange,
            StockProfile.industry,
            StockProfile.listed_at,
            StockProfile.delisted_at,
            StockProfile.pinyin,
            StockProfile.source,
            StockProfile.updated_at,
        )
        .where(
            (StockProfile.listed_at.is_(None) | (StockProfile.listed_at <= target)),
            (StockProfile.delisted_at.is_(None) | (StockProfile.delisted_at > target)),
        )
        .order_by(StockProfile.symbol)
    )
    with session_scope() as session:
        return [dict(row) for row in session.execute(statement).mappings()]


def fetch_daily_bars_for_date(
    target_date: str,
    symbols: Iterable[str],
) -> dict[str, dict[str, Any]]:
    symbol_list = tuple(symbols)
    if not symbol_list:
        return {}
    statement = select(
        DailyBar.symbol,
        DailyBar.date,
        DailyBar.open,
        DailyBar.high,
        DailyBar.low,
        DailyBar.close,
        DailyBar.volume,
        DailyBar.turnover,
        DailyBar.amplitude,
        DailyBar.change_rate,
        DailyBar.change_amount,
        DailyBar.turnover_rate,
        DailyBar.adjust_type,
        DailyBar.source,
        DailyBar.updated_at,
    ).where(
        DailyBar.date == _date(target_date),
        DailyBar.adjust_type == "none",
        DailyBar.symbol.in_(symbol_list),
    )
    with session_scope() as session:
        return {row["symbol"]: dict(row) for row in session.execute(statement).mappings()}


def fetch_stock_status_for_date(
    target_date: str,
    symbols: Iterable[str],
) -> dict[str, dict[str, Any]]:
    symbol_list = tuple(symbols)
    if not symbol_list:
        return {}
    statement = select(
        StockStatus.symbol,
        StockStatus.date,
        StockStatus.is_st,
        StockStatus.is_suspended,
        StockStatus.source,
        StockStatus.updated_at,
    ).where(
        StockStatus.date == _date(target_date),
        StockStatus.symbol.in_(symbol_list),
    )
    with session_scope() as session:
        return {row["symbol"]: dict(row) for row in session.execute(statement).mappings()}


def fetch_limit_prices_for_date(
    target_date: str,
    symbols: Iterable[str],
) -> dict[str, dict[str, Any]]:
    symbol_list = tuple(symbols)
    if not symbol_list:
        return {}
    statement = select(
        LimitPrice.symbol,
        LimitPrice.date,
        LimitPrice.up_limit,
        LimitPrice.down_limit,
        LimitPrice.source,
        LimitPrice.updated_at,
    ).where(
        LimitPrice.date == _date(target_date),
        LimitPrice.symbol.in_(symbol_list),
    )
    with session_scope() as session:
        return {row["symbol"]: dict(row) for row in session.execute(statement).mappings()}


def upsert_universe_members(
    universe_id: str,
    target_date: str,
    rows: Iterable[dict[str, Any]],
) -> int:
    now = datetime.now(timezone.utc)
    values = [
        {
            "universe_id": universe_id,
            "date": _date(target_date),
            "symbol": row["symbol"],
            "name": row["name"],
            "included": row["included"],
            "excluded_reason": row.get("excluded_reason"),
            "can_buy": row.get("can_buy", True),
            "can_sell": row.get("can_sell", True),
            "flags": row.get("flags") or [],
            "created_at": now,
        }
        for row in rows
    ]
    if not values:
        return 0
    statement = insert(UniverseMember)
    statement = statement.on_conflict_do_update(
        index_elements=[UniverseMember.universe_id, UniverseMember.date, UniverseMember.symbol],
        set_={
            "name": statement.excluded.name,
            "included": statement.excluded.included,
            "excluded_reason": statement.excluded.excluded_reason,
            "can_buy": statement.excluded.can_buy,
            "can_sell": statement.excluded.can_sell,
            "flags": statement.excluded.flags,
            "created_at": statement.excluded.created_at,
        },
    )
    with session_scope() as session:
        session.execute(statement, values)
    return len(values)


def fetch_universe_members(universe_id: str, target_date: str) -> list[dict[str, Any]]:
    statement = (
        select(
            UniverseMember.date,
            UniverseMember.universe_id,
            UniverseMember.symbol,
            UniverseMember.name,
            UniverseMember.included,
            UniverseMember.excluded_reason,
            UniverseMember.can_buy,
            UniverseMember.can_sell,
            UniverseMember.flags,
            UniverseMember.created_at,
        )
        .where(
            UniverseMember.universe_id == universe_id,
            UniverseMember.date == _date(target_date),
        )
        .order_by(UniverseMember.included.desc(), UniverseMember.symbol)
    )
    with session_scope() as session:
        return [dict(row) for row in session.execute(statement).mappings()]
