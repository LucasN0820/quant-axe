"""Runtime configuration for the QuantDash backend."""

from __future__ import annotations

import os


POSTGRES_DSN = os.environ.get(
    "POSTGRES_DSN",
    "postgresql://quantdash:quantdash@127.0.0.1:5432/quantdash",
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
TUSHARE_TOKEN = os.environ.get("TUSHARE_TOKEN", "")

CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "300"))

# APScheduler runtime control. When disabled the FastAPI app starts without
# any background jobs, which is the safe default for local development and
# unit tests.
SCHEDULER_ENABLED = os.environ.get("SCHEDULER_ENABLED", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# Refresh frequencies for the in-process scheduler. They are kept conservative
# to avoid hammering AkShare/NewsNow when running on a personal machine.
HOT_NEWS_REFRESH_MINUTES = int(os.environ.get("HOT_NEWS_REFRESH_MINUTES", "15"))
HOT_KEYWORDS_REFRESH_MINUTES = int(os.environ.get("HOT_KEYWORDS_REFRESH_MINUTES", "30"))
STOCK_PROFILE_REFRESH_HOURS = int(os.environ.get("STOCK_PROFILE_REFRESH_HOURS", "24"))
TRADE_CALENDAR_REFRESH_HOURS = int(os.environ.get("TRADE_CALENDAR_REFRESH_HOURS", "24"))
DAILY_BARS_CRON_HOUR = int(os.environ.get("DAILY_BARS_CRON_HOUR", "16"))
FINANCIALS_CRON_HOUR = int(os.environ.get("FINANCIALS_CRON_HOUR", "20"))

# Symbols refreshed by the scheduler's `daily_bars_refresh` and
# `financials_refresh` jobs. Keeping this list small keeps the personal-account
# Tushare quota usage predictable while still warming the most-watched names.
DAILY_REFRESH_WATCHLIST = tuple(
    symbol.strip()
    for symbol in os.environ.get(
        "DAILY_REFRESH_WATCHLIST",
        "600519,300750,688981,000001,601318",
    ).split(",")
    if symbol.strip()
)
