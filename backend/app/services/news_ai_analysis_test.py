"""Tests for News Center AI analysis helpers."""
# pylint: disable=line-too-long,missing-class-docstring

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from backend.app.services import news_ai_analysis
from backend.app.services.news_ai_analysis import (
    format_news_items,
    parse_analysis_content,
    run_analysis,
)
from backend.app.services.news_r2 import NewsSnapshot


class NewsAIAnalysisTest(unittest.TestCase):
    def test_parses_fenced_json_response(self) -> None:
        payload = parse_analysis_content(
            """```json
{"core_trends":"趋势","sentiment_controversy":"争议","signals":"信号","outlook_strategy":"观察"}
```"""
        )

        self.assertEqual("趋势", payload["core_trends"])
        self.assertEqual("观察", payload["outlook_strategy"])

    def test_formats_quantitative_context(self) -> None:
        rendered = format_news_items(
            [
                {
                    "source_name": "财联社热门",
                    "rank": 1,
                    "title": "算力需求变化",
                    "crawl_count": 2,
                    "rank_timeline": [{"time": "09:30", "rank": 3}, {"time": "10:00", "rank": 1}],
                }
            ]
        )

        self.assertIn("crawls=2", rendered)
        self.assertIn("09:30:3 -> 10:00:1", rendered)

    def test_skips_model_call_for_analyzed_snapshot_and_mode(self) -> None:
        snapshot = NewsSnapshot(
            key="news/2026-06-02.db",
            etag="etag-1",
            snapshot_date="2026-06-02",
            crawl_time="2026-06-02 10:00:00",
            stale=False,
            current_items=(),
            daily_items=(),
            source_status={},
        )
        with patch.object(news_ai_analysis, "get_analysis_items", return_value=(snapshot, [])), patch.object(
            news_ai_analysis.news_ai_repository,
            "has_analysis",
            return_value=True,
        ), patch.object(news_ai_analysis.news_ai_repository, "record_run") as record_run, patch.object(
            news_ai_analysis,
            "generate_analysis",
        ) as generate:
            result = run_analysis(
                node_key="morning_session",
                scheduled_time="10:00",
                analysis_mode="current",
                execution_time=datetime(2026, 6, 2, 2, 0, tzinfo=timezone.utc),
                calendar_degraded=False,
            )

        self.assertEqual("skipped_unchanged_snapshot", result["status"])
        generate.assert_not_called()
        record_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
