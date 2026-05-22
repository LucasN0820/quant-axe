from __future__ import annotations

import unittest

from backend.app.services.news_data import normalize_news_datetime, parse_news_datetime


class NewsDataTest(unittest.TestCase):
    """News timestamp normalization tests."""

    def test_parse_news_datetime_accepts_millisecond_epoch(self) -> None:
        self.assertEqual(1779417556.0, parse_news_datetime("1779417556216"))

    def test_normalize_news_datetime_outputs_iso_timestamp(self) -> None:
        self.assertEqual(
            "2026-05-22T02:39:16+00:00",
            normalize_news_datetime("1779417556216"),
        )


if __name__ == "__main__":
    unittest.main()
