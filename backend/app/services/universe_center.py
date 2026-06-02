"""Universe Center models, providers, filters, and serving helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any
from uuid import uuid4

from backend.app.services.market_data import stock_code_name_rows, stringify
from backend.app.services.reference_utils import infer_exchange, normalize_provider_date, utc_now
from backend.app.db.repositories.universes import (
    delete_universe,
    fetch_daily_bars_for_date,
    fetch_limit_prices_for_date,
    fetch_stock_profiles_as_of,
    fetch_stock_status_for_date,
    fetch_universe,
    fetch_universe_members,
    fetch_universes,
    upsert_universe,
    upsert_universe_members,
)
from backend.app.services.tushare_data import fetch_tushare_index_members


BASE_UNIVERSES = {"all_a", "hs300", "zz500", "zz1000", "custom"}
INDEX_BASE_CODES = {
    "hs300": "000300.SH",
    "zz500": "000905.SH",
    "zz1000": "000852.SH",
}
FILTER_TYPES = {
    "st",
    "suspension",
    "listed_days",
    "liquidity",
    "price",
    "limit_up_down",
}


@dataclass
class FilterContext:
    """Point-in-time data needed by universe filters."""

    target_date: str
    status_by_symbol: dict[str, dict[str, Any]] = field(default_factory=dict)
    daily_bar_by_symbol: dict[str, dict[str, Any]] = field(default_factory=dict)
    limit_price_by_symbol: dict[str, dict[str, Any]] = field(default_factory=dict)


def list_universes() -> dict[str, Any]:
    try:
        rows = fetch_universes()
    except Exception as error:  # pylint: disable=broad-exception-caught
        return {
            "source": "postgresql.universes",
            "status": "unavailable",
            "message": str(error),
            "data": builtin_universes(),
        }
    return {
        "source": "postgresql.universes",
        "status": "ready",
        "updated_at": utc_now(),
        "data": merge_builtin_universes(rows),
    }


def create_universe(payload: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()
    universe = normalize_universe_payload(payload, created_at=now, updated_at=now)
    upsert_universe(universe)
    return universe


def get_universe(universe_id: str) -> dict[str, Any]:
    universe = resolve_universe(universe_id)
    return {"source": "universe_center", "status": "ready", "data": universe}


def update_universe(universe_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    existing = resolve_universe(universe_id, include_builtin=False)
    updated = {
        **existing,
        "name": payload.get("name", existing["name"]),
        "base": payload.get("base", existing["base"]),
        "filters": payload.get("filters", existing["filters"]),
        "updated_at": utc_now(),
    }
    validate_universe(updated)
    upsert_universe(updated)
    return updated


def remove_universe(universe_id: str) -> dict[str, Any]:
    deleted = delete_universe(universe_id)
    if not deleted:
        raise ValueError(f"unknown universe: {universe_id}")
    return {"id": universe_id, "status": "deleted"}


def preview_universe(universe_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    universe = resolve_universe(universe_id)
    if any(key in payload for key in ("name", "base", "filters")):
        universe = {
            **universe,
            "name": payload.get("name", universe["name"]),
            "base": payload.get("base", universe["base"]),
            "filters": payload.get("filters", universe["filters"]),
        }
        validate_universe(universe)
    target_date = parse_payload_date(payload)
    members = generate_members(universe, target_date)
    return universe_members_payload(universe, target_date, members, source="generated")


def snapshot_universe(universe_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    universe = resolve_universe(universe_id)
    target_date = parse_payload_date(payload)
    members = generate_members(universe, target_date)
    saved = upsert_universe_members(universe["id"], target_date, members)
    return {
        **universe_members_payload(universe, target_date, members, source="snapshot"),
        "saved": saved,
    }


def universe_stocks(universe_id: str, target_date: str) -> dict[str, Any]:
    universe = resolve_universe(universe_id)
    date.fromisoformat(target_date)
    rows = fetch_universe_members(universe["id"], target_date)
    if rows:
        return universe_members_payload(universe, target_date, rows, source="snapshot")
    members = generate_members(universe, target_date)
    return universe_members_payload(universe, target_date, members, source="generated")


def generate_members(universe: dict[str, Any], target_date: str) -> list[dict[str, Any]]:
    date.fromisoformat(target_date)
    candidates = base_universe_members(universe["base"], target_date)
    symbols = [row["symbol"] for row in candidates]
    context = FilterContext(
        target_date=target_date,
        status_by_symbol=safe_fetch(fetch_stock_status_for_date, target_date, symbols),
        daily_bar_by_symbol=safe_fetch(fetch_daily_bars_for_date, target_date, symbols),
        limit_price_by_symbol=safe_fetch(fetch_limit_prices_for_date, target_date, symbols),
    )
    return apply_filter_pipeline(candidates, universe.get("filters") or [], context)


def base_universe_members(base: str, target_date: str) -> list[dict[str, Any]]:
    if base == "all_a":
        rows = safe_fetch(fetch_stock_profiles_as_of, target_date)
        if not rows:
            rows = [
                {
                    "symbol": stringify(row.get("code")),
                    "name": stringify(row.get("name")) or stringify(row.get("code")),
                    "exchange": infer_exchange(stringify(row.get("code"))),
                    "listed_at": None,
                    "source": "akshare.stock_info_a_code_name",
                }
                for row in stock_code_name_rows()
                if stringify(row.get("code"))
            ]
        return normalize_candidates(rows)
    if base in INDEX_BASE_CODES:
        rows = fetch_tushare_index_members(INDEX_BASE_CODES[base], target_date)
        return normalize_candidates(rows)
    if base == "custom":
        return []
    raise ValueError(f"unknown base universe: {base}")


def apply_filter_pipeline(
    candidates: list[dict[str, Any]],
    filters: list[dict[str, Any]],
    context: FilterContext,
) -> list[dict[str, Any]]:
    members = [
        {
            "date": context.target_date,
            "symbol": row["symbol"],
            "name": row.get("name") or row["symbol"],
            "included": True,
            "excluded_reason": None,
            "can_buy": True,
            "can_sell": True,
            "flags": [],
            "listed_at": row.get("listed_at"),
        }
        for row in candidates
    ]
    for filter_config in filters:
        filter_type = filter_config.get("type")
        if filter_type == "st":
            apply_st_filter(members, context)
        elif filter_type == "suspension":
            apply_suspension_filter(members, context)
        elif filter_type == "listed_days":
            apply_listed_days_filter(members, context, int(filter_config.get("min_days", 0)))
        elif filter_type == "liquidity":
            apply_liquidity_filter(members, context, float(filter_config.get("min_turnover", 0)))
        elif filter_type == "price":
            apply_price_filter(
                members,
                context,
                filter_config.get("min_price"),
                filter_config.get("max_price"),
            )
        elif filter_type == "limit_up_down":
            apply_limit_up_down_filter(members, context)
    return sorted(
        (strip_internal_fields(member) for member in members),
        key=lambda item: item["symbol"],
    )


def apply_st_filter(members: list[dict[str, Any]], context: FilterContext) -> None:
    for member in members:
        status = context.status_by_symbol.get(member["symbol"], {})
        if status.get("is_st"):
            exclude(member, "ST")


def apply_suspension_filter(members: list[dict[str, Any]], context: FilterContext) -> None:
    for member in members:
        status = context.status_by_symbol.get(member["symbol"], {})
        if status.get("is_suspended"):
            exclude(member, "停牌")


def apply_listed_days_filter(
    members: list[dict[str, Any]],
    context: FilterContext,
    min_days: int,
) -> None:
    if min_days <= 0:
        return
    target = date.fromisoformat(context.target_date)
    for member in members:
        listed_at = normalize_provider_date(member.get("listed_at"))
        if listed_at is None:
            continue
        listed_days = (target - date.fromisoformat(listed_at)).days
        if listed_days < min_days:
            exclude(member, f"上市不足{min_days}天")


def apply_liquidity_filter(
    members: list[dict[str, Any]],
    context: FilterContext,
    min_turnover: float,
) -> None:
    if min_turnover <= 0:
        return
    for member in members:
        daily_bar = context.daily_bar_by_symbol.get(member["symbol"], {})
        turnover = daily_bar.get("turnover")
        if turnover is not None and float(turnover) < min_turnover:
            exclude(member, f"成交额低于{format_number(min_turnover)}")


def apply_price_filter(
    members: list[dict[str, Any]],
    context: FilterContext,
    min_price: Any,
    max_price: Any,
) -> None:
    low = float(min_price) if min_price is not None else None
    high = float(max_price) if max_price is not None else None
    for member in members:
        daily_bar = context.daily_bar_by_symbol.get(member["symbol"], {})
        close = daily_bar.get("close")
        if close is None:
            continue
        price = float(close)
        if low is not None and price < low:
            exclude(member, f"价格低于{format_number(low)}")
        elif high is not None and price > high:
            exclude(member, f"价格高于{format_number(high)}")


def apply_limit_up_down_filter(members: list[dict[str, Any]], context: FilterContext) -> None:
    for member in members:
        daily_bar = context.daily_bar_by_symbol.get(member["symbol"], {})
        limit_price = context.limit_price_by_symbol.get(member["symbol"], {})
        close = daily_bar.get("close")
        up_limit = limit_price.get("up_limit")
        down_limit = limit_price.get("down_limit")
        if close is None:
            continue
        if up_limit is not None and float(close) >= float(up_limit):
            member["can_buy"] = False
            member["flags"].append("limit_up")
        if down_limit is not None and float(close) <= float(down_limit):
            member["can_sell"] = False
            member["flags"].append("limit_down")


def exclude(member: dict[str, Any], reason: str) -> None:
    if member["included"]:
        member["included"] = False
        member["excluded_reason"] = reason


def normalize_universe_payload(
    payload: dict[str, Any],
    *,
    created_at: str,
    updated_at: str,
) -> dict[str, Any]:
    universe = {
        "id": payload.get("id") or f"universe-{uuid4().hex[:12]}",
        "name": payload.get("name") or "未命名股票池",
        "base": payload.get("base") or "hs300",
        "filters": payload.get("filters") or [],
        "created_at": created_at,
        "updated_at": updated_at,
    }
    validate_universe(universe)
    return universe


def validate_universe(universe: dict[str, Any]) -> None:
    if universe.get("base") not in BASE_UNIVERSES:
        raise ValueError(f"unknown base universe: {universe.get('base')}")
    if not isinstance(universe.get("filters"), list):
        raise ValueError("filters must be a list")
    for filter_config in universe["filters"]:
        filter_type = filter_config.get("type")
        if filter_type not in FILTER_TYPES:
            raise ValueError(f"unknown universe filter: {filter_type}")


def resolve_universe(universe_id: str, include_builtin: bool = True) -> dict[str, Any]:
    if include_builtin:
        for universe in builtin_universes():
            if universe["id"] == universe_id:
                return universe
    universe = fetch_universe(universe_id)
    if universe is None:
        raise ValueError(f"unknown universe: {universe_id}")
    return universe


def builtin_universes() -> list[dict[str, Any]]:
    now = "system"
    return [
        {
            "id": "builtin-hs300-basic",
            "name": "沪深300基础池",
            "base": "hs300",
            "filters": [{"type": "st"}, {"type": "suspension"}],
            "created_at": now,
            "updated_at": now,
        }
    ]


def merge_builtin_universes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    builtin = {row["id"]: row for row in builtin_universes()}
    for row in rows:
        builtin[row["id"]] = row
    return list(builtin.values())


def normalize_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    seen = set()
    for row in rows:
        symbol = stringify(row.get("symbol") or row.get("code"))
        if len(symbol) != 6 or symbol in seen:
            continue
        seen.add(symbol)
        normalized.append(
            {
                "symbol": symbol,
                "name": stringify(row.get("name")) or symbol,
                "exchange": row.get("exchange") or infer_exchange(symbol),
                "listed_at": normalize_provider_date(row.get("listed_at")),
            }
        )
    return sorted(normalized, key=lambda item: item["symbol"])


def strip_internal_fields(member: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in member.items() if key != "listed_at"}


def parse_payload_date(payload: dict[str, Any]) -> str:
    target_date = payload.get("date")
    if not target_date:
        raise ValueError("date is required")
    return date.fromisoformat(target_date).isoformat()


def format_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(value)


def universe_members_payload(
    universe: dict[str, Any],
    target_date: str,
    members: list[dict[str, Any]],
    *,
    source: str,
) -> dict[str, Any]:
    included = sum(1 for row in members if row.get("included"))
    return {
        "source": source,
        "status": "ready",
        "universe": universe,
        "date": target_date,
        "total": len(members),
        "included": included,
        "excluded": len(members) - included,
        "updated_at": utc_now(),
        "data": members,
    }


def safe_fetch(function, *args):
    try:
        return function(*args)
    except Exception:  # pylint: disable=broad-exception-caught
        return {} if function.__name__.startswith("fetch_") else []
