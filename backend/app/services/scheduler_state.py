"""Lightweight scheduler state holder shared across modules.

This module exists to break a circular import between the data_center
(which exposes scheduler status through `/api/data/health`) and the
scheduler module (which calls into data_center jobs). Only plain data
containers live here, no heavy imports.
"""

from __future__ import annotations

from typing import Any

from backend.app.services.config import SCHEDULER_ENABLED
from backend.app.services.reference_utils import utc_now


class JobRegistry:
    """Track the most recent invocation of each scheduled job."""

    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {}

    def remember(
        self,
        name: str,
        status: str,
        started_at: str,
        *,
        error: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.records[name] = {
            "name": name,
            "status": status,
            "last_run_at": started_at,
            "error": error,
            "details": details,
        }

    def snapshot(self) -> list[dict[str, Any]]:
        return list(self.records.values())


registry = JobRegistry()
runtime_state: dict[str, Any] = {"running": False}


def scheduler_status() -> dict[str, Any]:
    return {
        "enabled": SCHEDULER_ENABLED,
        "running": bool(runtime_state.get("running")),
        "calendar_degraded": bool(runtime_state.get("calendar_degraded")),
        "jobs": registry.snapshot(),
        "checked_at": utc_now(),
    }
