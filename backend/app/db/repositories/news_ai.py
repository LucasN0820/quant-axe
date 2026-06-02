"""SQLAlchemy repository for News Center AI analysis persistence."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from backend.app.db.engine import session_scope
from backend.app.db.models import (
    HotNewsAIAnalysis,
    HotNewsAIAnalysisRun,
    TradeCalendar,
)


def insert_analysis(payload: dict[str, Any]) -> None:
    """Persist one successful AI analysis."""

    with session_scope() as session:
        session.add(HotNewsAIAnalysis(**payload))


def fetch_latest_analysis() -> dict[str, Any] | None:
    """Return the most recently generated successful analysis."""

    statement = (
        select(
            HotNewsAIAnalysis.id,
            HotNewsAIAnalysis.snapshot_key,
            HotNewsAIAnalysis.snapshot_etag,
            HotNewsAIAnalysis.snapshot_date,
            HotNewsAIAnalysis.snapshot_crawl_time,
            HotNewsAIAnalysis.node_key,
            HotNewsAIAnalysis.analysis_mode,
            HotNewsAIAnalysis.model,
            HotNewsAIAnalysis.content,
            HotNewsAIAnalysis.analyzed_news,
            HotNewsAIAnalysis.generated_at,
        )
        .order_by(HotNewsAIAnalysis.generated_at.desc(), HotNewsAIAnalysis.id.desc())
        .limit(1)
    )
    with session_scope() as session:
        row = session.execute(statement).mappings().one_or_none()
        return dict(row) if row is not None else None


def has_analysis(snapshot_key: str, snapshot_etag: str, analysis_mode: str) -> bool:
    """Return whether a snapshot and mode pair already has a report."""

    statement = (
        select(HotNewsAIAnalysis.id)
        .where(
            HotNewsAIAnalysis.snapshot_key == snapshot_key,
            HotNewsAIAnalysis.snapshot_etag == snapshot_etag,
            HotNewsAIAnalysis.analysis_mode == analysis_mode,
        )
        .limit(1)
    )
    with session_scope() as session:
        return session.execute(statement).scalar_one_or_none() is not None


def has_run(execution_date: date, node_key: str, scheduled_time: str) -> bool:
    """Return whether a timeline node has already run for its date."""

    statement = (
        select(HotNewsAIAnalysisRun.id)
        .where(
            HotNewsAIAnalysisRun.execution_date == execution_date,
            HotNewsAIAnalysisRun.node_key == node_key,
            HotNewsAIAnalysisRun.scheduled_time == scheduled_time,
        )
        .limit(1)
    )
    with session_scope() as session:
        return session.execute(statement).scalar_one_or_none() is not None


def record_run(payload: dict[str, Any]) -> None:
    """Persist or update one timeline execution outcome."""

    statement = insert(HotNewsAIAnalysisRun).values(payload)
    statement = statement.on_conflict_do_update(
        index_elements=[
            HotNewsAIAnalysisRun.execution_date,
            HotNewsAIAnalysisRun.node_key,
            HotNewsAIAnalysisRun.scheduled_time,
        ],
        set_={
            "analysis_mode": statement.excluded.analysis_mode,
            "status": statement.excluded.status,
            "snapshot_key": statement.excluded.snapshot_key,
            "snapshot_etag": statement.excluded.snapshot_etag,
            "calendar_degraded": statement.excluded.calendar_degraded,
            "error": statement.excluded.error,
            "started_at": statement.excluded.started_at,
            "finished_at": statement.excluded.finished_at,
        },
    )
    with session_scope() as session:
        session.execute(statement)


def fetch_trade_calendar_day(target_date: date, exchange: str = "SSE") -> bool | None:
    """Return the stored trading-day state, or None when it is absent."""

    statement = select(TradeCalendar.is_open).where(
        TradeCalendar.exchange == exchange,
        TradeCalendar.date == target_date,
    )
    with session_scope() as session:
        return session.execute(statement).scalar_one_or_none()
