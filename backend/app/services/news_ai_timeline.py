"""A-share-aware timeline resolver for News Center AI analysis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from backend.app.db.repositories import news_ai as news_ai_repository
from backend.app.services.config import AI_ANALYSIS_TIMELINE_PATH


SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


@dataclass(frozen=True)
class TimelineNode:
    """One AI analysis node scheduled for the current minute."""

    key: str
    scheduled_time: str
    analysis_mode: str


@dataclass(frozen=True)
class TradingDayState:
    """Trading-day decision together with its fallback signal."""

    is_open: bool
    degraded: bool


def resolve_due_nodes(
    now: datetime | None = None,
    *,
    trading_day_state: TradingDayState | None = None,
    timeline: dict[str, Any] | None = None,
) -> tuple[TradingDayState, list[TimelineNode]]:
    """Return timeline nodes matching the current Shanghai minute."""

    current_time = (now or datetime.now(SHANGHAI_TZ)).astimezone(SHANGHAI_TZ)
    config = timeline or load_timeline()
    current_hhmm = current_time.strftime("%H:%M")
    possible_times = {
        str(scheduled_time)
        for plan_key in ("trading_day", "non_trading_day")
        for raw_node in config.get(plan_key, [])
        for scheduled_time in raw_node.get("times", [])
    }
    if current_hhmm not in possible_times:
        return trading_day_state or TradingDayState(is_open=False, degraded=False), []

    state = trading_day_state or resolve_trading_day(current_time)
    plan_key = "trading_day" if state.is_open else "non_trading_day"
    nodes = []
    for raw_node in config.get(plan_key, []):
        for scheduled_time in raw_node.get("times", []):
            if scheduled_time == current_hhmm:
                nodes.append(
                    TimelineNode(
                        key=str(raw_node["node"]),
                        scheduled_time=str(scheduled_time),
                        analysis_mode=str(raw_node["mode"]),
                    )
                )
    return state, nodes


def resolve_trading_day(now: datetime | None = None) -> TradingDayState:
    """Resolve SSE trading-day state with AkShare then weekday fallback."""

    current_time = (now or datetime.now(SHANGHAI_TZ)).astimezone(SHANGHAI_TZ)
    target_date = current_time.date()
    try:
        stored = news_ai_repository.fetch_trade_calendar_day(target_date)
    except Exception:  # pylint: disable=broad-exception-caught
        stored = None
    if stored is not None:
        return TradingDayState(is_open=stored, degraded=False)

    try:
        from backend.app.services.data_center import (  # pylint: disable=import-outside-toplevel
            refresh_trade_calendar,
        )

        refresh_trade_calendar()
        stored = news_ai_repository.fetch_trade_calendar_day(target_date)
    except Exception:  # pylint: disable=broad-exception-caught
        stored = None
    if stored is not None:
        return TradingDayState(is_open=stored, degraded=False)
    return TradingDayState(is_open=target_date.weekday() < 5, degraded=True)


def load_timeline(path: str = AI_ANALYSIS_TIMELINE_PATH) -> dict[str, Any]:
    """Load the configured YAML timeline."""

    import yaml  # pylint: disable=import-outside-toplevel

    with Path(path).open(encoding="utf-8") as timeline_file:
        config = yaml.safe_load(timeline_file) or {}
    validate_timeline(config)
    return config


def validate_timeline(config: dict[str, Any]) -> None:
    """Reject malformed timeline configuration at startup or in tests."""

    for plan_key in ("trading_day", "non_trading_day"):
        plan = config.get(plan_key)
        if not isinstance(plan, list):
            raise ValueError(f"timeline is missing list: {plan_key}")
        for node in plan:
            if not isinstance(node, dict) or not node.get("node"):
                raise ValueError(f"timeline {plan_key} has a node without a key")
            if node.get("mode") not in {"current", "daily"}:
                raise ValueError(f"timeline node {node.get('node')} has an invalid mode")
            times = node.get("times")
            if not isinstance(times, list) or not times:
                raise ValueError(f"timeline node {node.get('node')} has no times")
            for value in times:
                _validate_time(str(value))


def _validate_time(value: str) -> None:
    try:
        datetime.strptime(value, "%H:%M")
    except ValueError as error:
        raise ValueError(f"invalid timeline time: {value}") from error
