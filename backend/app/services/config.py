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
QUOTE_CACHE_TTL_SECONDS = int(os.environ.get("QUOTE_CACHE_TTL_SECONDS", "3"))
INDEX_CACHE_TTL_SECONDS = int(os.environ.get("INDEX_CACHE_TTL_SECONDS", "5"))
QUOTE_BATCH_MAX_SYMBOLS = int(os.environ.get("QUOTE_BATCH_MAX_SYMBOLS", "50"))
QUOTE_PROVIDER_MAX_WORKERS = int(os.environ.get("QUOTE_PROVIDER_MAX_WORKERS", "3"))

NEWS_R2_ENDPOINT_URL = os.environ.get("NEWS_R2_ENDPOINT_URL", "")
NEWS_R2_BUCKET_NAME = os.environ.get("NEWS_R2_BUCKET_NAME", "")
NEWS_R2_ACCESS_KEY_ID = os.environ.get("NEWS_R2_ACCESS_KEY_ID", "")
NEWS_R2_SECRET_ACCESS_KEY = os.environ.get("NEWS_R2_SECRET_ACCESS_KEY", "")
NEWS_R2_REGION = os.environ.get("NEWS_R2_REGION", "")
NEWS_R2_PREFIX = os.environ.get("NEWS_R2_PREFIX", "news").strip("/")
NEWS_R2_CACHE_TTL_SECONDS = int(os.environ.get("NEWS_R2_CACHE_TTL_SECONDS", "300"))
HOT_NEWS_SOURCES = tuple(
    source.strip()
    for source in os.environ.get(
        "HOT_NEWS_SOURCES",
        "cls-hot,wallstreetcn-hot,ifeng",
    ).split(",")
    if source.strip()
)

AI_ANALYSIS_ENABLED = os.environ.get("AI_ANALYSIS_ENABLED", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
AI_ANALYSIS_TIMELINE_PATH = os.environ.get(
    "AI_ANALYSIS_TIMELINE_PATH",
    "backend/config/news_ai_timeline.yaml",
)
AI_ANALYSIS_MAX_NEWS = int(os.environ.get("AI_ANALYSIS_MAX_NEWS", "150"))
AI_MODEL = os.environ.get("AI_MODEL", "deepseek/deepseek-v4-flash")
AI_API_KEY = os.environ.get("AI_API_KEY", "")
AI_API_BASE = os.environ.get("AI_API_BASE", "")
AI_TIMEOUT_SECONDS = int(os.environ.get("AI_TIMEOUT_SECONDS", "120"))
AI_TEMPERATURE = float(os.environ.get("AI_TEMPERATURE", "1.0"))
AI_MAX_TOKENS = int(os.environ.get("AI_MAX_TOKENS", "5000"))
AI_NUM_RETRIES = int(os.environ.get("AI_NUM_RETRIES", "1"))

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
# to avoid hammering AkShare when running on a personal machine.
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
