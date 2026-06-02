"""APScheduler-based background scheduler for data refresh jobs."""
# pylint: disable=duplicate-code

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.app.services.config import (
    AI_ANALYSIS_ENABLED,
    DAILY_BARS_CRON_HOUR,
    DAILY_REFRESH_WATCHLIST,
    FINANCIALS_CRON_HOUR,
    HOT_KEYWORDS_REFRESH_MINUTES,
    NEWS_R2_CACHE_TTL_SECONDS,
    SCHEDULER_ENABLED,
    STOCK_PROFILE_REFRESH_HOURS,
    TRADE_CALENDAR_REFRESH_HOURS,
)
from backend.app.services.reference_utils import utc_now
from backend.app.services.scheduler_state import (
    registry,
    runtime_state,
    scheduler_status as _scheduler_status,
)


WATCHLIST_FOR_DAILY_REFRESH = DAILY_REFRESH_WATCHLIST


_scheduler: Any = None  # pylint: disable=invalid-name


def scheduler_status() -> dict[str, Any]:
    return _scheduler_status()


def start_scheduler() -> dict[str, Any]:
    """Start the APScheduler background scheduler if enabled."""
    global _scheduler  # pylint: disable=global-statement
    if not SCHEDULER_ENABLED:
        return {"enabled": False, "reason": "SCHEDULER_ENABLED is false"}
    if _scheduler is not None:
        return {"enabled": True, "status": "already_running"}

    from apscheduler.schedulers.background import (  # pylint: disable=import-outside-toplevel
        BackgroundScheduler,
    )
    from apscheduler.triggers.cron import (  # pylint: disable=import-outside-toplevel
        CronTrigger,
    )
    from apscheduler.triggers.interval import (  # pylint: disable=import-outside-toplevel
        IntervalTrigger,
    )

    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

    scheduler.add_job(
        run_hot_news_refresh,
        IntervalTrigger(seconds=NEWS_R2_CACHE_TTL_SECONDS),
        id="hot_news_refresh",
        name="hot_news_refresh",
        max_instances=1,
        replace_existing=True,
    )
    if AI_ANALYSIS_ENABLED:
        scheduler.add_job(
            run_hot_news_ai_analysis,
            IntervalTrigger(minutes=1),
            id="hot_news_ai_analysis",
            name="hot_news_ai_analysis",
            max_instances=1,
            replace_existing=True,
        )
    scheduler.add_job(
        run_hot_keywords_refresh,
        IntervalTrigger(minutes=HOT_KEYWORDS_REFRESH_MINUTES),
        id="hot_keywords_refresh",
        name="hot_keywords_refresh",
        max_instances=1,
        replace_existing=True,
    )
    scheduler.add_job(
        run_stock_profile_refresh,
        IntervalTrigger(hours=STOCK_PROFILE_REFRESH_HOURS),
        id="stock_profile_refresh",
        name="stock_profile_refresh",
        max_instances=1,
        replace_existing=True,
    )
    scheduler.add_job(
        run_trade_calendar_refresh,
        IntervalTrigger(hours=TRADE_CALENDAR_REFRESH_HOURS),
        id="trade_calendar_refresh",
        name="trade_calendar_refresh",
        max_instances=1,
        replace_existing=True,
    )
    scheduler.add_job(
        run_daily_bars_refresh,
        CronTrigger(day_of_week="mon-fri", hour=DAILY_BARS_CRON_HOUR, minute=0),
        id="daily_bars_refresh",
        name="daily_bars_refresh",
        max_instances=1,
        replace_existing=True,
    )
    scheduler.add_job(
        run_financials_refresh,
        CronTrigger(day_of_week="mon-fri", hour=FINANCIALS_CRON_HOUR, minute=0),
        id="financials_refresh",
        name="financials_refresh",
        max_instances=1,
        replace_existing=True,
    )

    scheduler.start()
    _scheduler = scheduler
    runtime_state["running"] = True
    return {"enabled": True, "status": "started", "started_at": utc_now()}


def stop_scheduler() -> None:
    global _scheduler  # pylint: disable=global-statement
    if _scheduler is None:
        return
    try:
        _scheduler.shutdown(wait=False)
    finally:
        _scheduler = None
        runtime_state["running"] = False


def run_hot_news_refresh() -> None:
    track("hot_news_refresh", _refresh_hot_news)


def run_hot_keywords_refresh() -> None:
    track("hot_keywords_refresh", _refresh_hot_keywords)


def run_hot_news_ai_analysis() -> None:
    track("hot_news_ai_analysis", _refresh_hot_news_ai_analysis)


def run_stock_profile_refresh() -> None:
    track("stock_profile_refresh", _refresh_stock_profiles)


def run_trade_calendar_refresh() -> None:
    track("trade_calendar_refresh", _refresh_trade_calendar)


def run_daily_bars_refresh() -> None:
    track("daily_bars_refresh", _refresh_daily_bars)


def run_financials_refresh() -> None:
    track("financials_refresh", _refresh_financials)


def track(name: str, action) -> None:
    started_at = datetime.utcnow().isoformat(timespec="seconds")
    try:
        result = action()
        if isinstance(result, dict) and "calendar_degraded" in result:
            runtime_state["calendar_degraded"] = bool(result["calendar_degraded"])
        registry.remember(
            name,
            "ok",
            started_at,
            details=result if isinstance(result, dict) else None,
        )
    except Exception as error:  # pylint: disable=broad-exception-caught
        registry.remember(name, "failed", started_at, error=str(error))


def _refresh_hot_news() -> dict[str, Any]:
    from backend.app.services.news_r2 import refresh_snapshot  # pylint: disable=import-outside-toplevel

    snapshot = refresh_snapshot(force=True)
    return {
        "snapshot_key": snapshot.key,
        "snapshot_etag": snapshot.etag,
        "stale": snapshot.stale,
    }


def _refresh_hot_keywords() -> None:
    from backend.app.services.sentiment_data import (  # pylint: disable=import-outside-toplevel
        get_hot_keywords,
    )

    get_hot_keywords(limit=50)


def _refresh_hot_news_ai_analysis() -> dict[str, Any]:
    from backend.app.services.news_ai_analysis import (  # pylint: disable=import-outside-toplevel
        run_due_analyses,
    )

    return run_due_analyses()


def _refresh_stock_profiles() -> None:
    from backend.app.services.data_center import (  # pylint: disable=import-outside-toplevel
        refresh_stock_profiles,
        refresh_tushare_stock_profiles,
    )
    from backend.app.services.search_data import (  # pylint: disable=import-outside-toplevel
        reset_search_index,
    )

    try:
        refresh_tushare_stock_profiles()
    except Exception:  # pylint: disable=broad-exception-caught
        # Tushare may be missing or hit rate limits; AkShare profiles are the
        # baseline source so we still attempt to refresh them.
        pass
    refresh_stock_profiles()
    reset_search_index()


def _refresh_trade_calendar() -> None:
    from backend.app.services.data_center import (  # pylint: disable=import-outside-toplevel
        refresh_trade_calendar,
    )

    refresh_trade_calendar()


def _refresh_daily_bars() -> None:
    from backend.app.services.data_center import (  # pylint: disable=import-outside-toplevel
        get_served_kline,
    )

    for symbol in WATCHLIST_FOR_DAILY_REFRESH:
        for adjust in ("none", "qfq", "hfq"):
            try:
                get_served_kline(symbol, "daily", adjust=adjust)
            except Exception:  # pylint: disable=broad-exception-caught
                continue


def _refresh_financials() -> None:
    from backend.app.services.financials_data import (  # pylint: disable=import-outside-toplevel
        get_financial_metrics,
    )

    for symbol in WATCHLIST_FOR_DAILY_REFRESH:
        try:
            get_financial_metrics(symbol)
        except Exception:  # pylint: disable=broad-exception-caught
            continue
