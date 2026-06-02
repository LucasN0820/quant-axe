"""Tests for the A-share News Center AI timeline."""
# pylint: disable=line-too-long,missing-class-docstring

from __future__ import annotations

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.app.services.news_ai_timeline import (
    TradingDayState,
    resolve_due_nodes,
    validate_timeline,
)


SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
TIMELINE = {
    "trading_day": [
        {"node": "pre_market", "times": ["09:20"], "mode": "daily"},
        {"node": "morning_session", "times": ["10:00", "10:30", "11:00", "11:30"], "mode": "current"},
        {"node": "midday_summary", "times": ["12:00"], "mode": "daily"},
        {"node": "afternoon_session", "times": ["13:30", "14:00", "14:30", "15:00"], "mode": "current"},
        {"node": "closing_summary", "times": ["15:30"], "mode": "daily"},
    ],
    "non_trading_day": [
        {"node": "non_trading_morning", "times": ["09:30"], "mode": "daily"},
    ],
}


class NewsAITimelineTest(unittest.TestCase):
    def test_resolves_morning_session(self) -> None:
        _, nodes = resolve_due_nodes(
            datetime(2026, 6, 2, 10, 30, tzinfo=SHANGHAI_TZ),
            trading_day_state=TradingDayState(is_open=True, degraded=False),
            timeline=TIMELINE,
        )

        self.assertEqual([("morning_session", "current")], [(node.key, node.analysis_mode) for node in nodes])

    def test_does_not_run_during_lunch_break(self) -> None:
        _, nodes = resolve_due_nodes(
            datetime(2026, 6, 2, 12, 30, tzinfo=SHANGHAI_TZ),
            trading_day_state=TradingDayState(is_open=True, degraded=False),
            timeline=TIMELINE,
        )

        self.assertEqual([], nodes)

    def test_uses_non_trading_plan(self) -> None:
        _, nodes = resolve_due_nodes(
            datetime(2026, 6, 6, 9, 30, tzinfo=SHANGHAI_TZ),
            trading_day_state=TradingDayState(is_open=False, degraded=False),
            timeline=TIMELINE,
        )

        self.assertEqual(["non_trading_morning"], [node.key for node in nodes])

    def test_rejects_invalid_modes(self) -> None:
        with self.assertRaises(ValueError):
            validate_timeline(
                {
                    "trading_day": [{"node": "bad", "times": ["09:20"], "mode": "weekly"}],
                    "non_trading_day": [],
                }
            )


if __name__ == "__main__":
    unittest.main()
