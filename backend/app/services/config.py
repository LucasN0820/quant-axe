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
