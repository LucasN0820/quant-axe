from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.app.services import sentiment_data


def _make_news(items: list[dict]) -> dict:
    return {"source": "newsnow", "status": "ready", "data": items}


class SentimentDataTest(unittest.TestCase):
    """Hot keyword extraction tests."""

    def test_unavailable_when_no_news(self) -> None:
        empty_payload = {"source": "newsnow", "status": "unavailable", "data": []}
        with patch.object(sentiment_data, "get_hot_news", return_value=empty_payload):
            with patch.object(sentiment_data, "insert_hot_keywords"), \
                patch.object(sentiment_data, "save_raw_payload"):
                payload = sentiment_data.get_hot_keywords()
        self.assertEqual("unavailable", payload["status"])
        self.assertEqual([], payload["data"])

    def test_extracts_recurring_chinese_tokens(self) -> None:
        # The regex extracts the greedy non-overlapping CJK runs (length 2-5),
        # so "新能源汽车" surfaces as a single token across multiple headlines.
        news = _make_news(
            [
                {"title": "新能源汽车 产业链景气度持续上行", "source_id": "cls-hot"},
                {"title": "新能源汽车 销量再创新高", "source_id": "wallstreetcn-hot"},
                {"title": "新能源汽车 板块领涨大盘", "source_id": "thepaper"},
            ]
        )
        with patch.object(sentiment_data, "get_hot_news", return_value=news):
            with patch.object(sentiment_data, "insert_hot_keywords"), \
                patch.object(sentiment_data, "save_raw_payload"):
                payload = sentiment_data.get_hot_keywords()
        words = [item["word"] for item in payload["data"]]
        self.assertIn("新能源汽车", words)
        self.assertEqual("ready", payload["status"])

    def test_drops_singletons_below_minimum_frequency(self) -> None:
        news = _make_news(
            [
                {"title": "光伏行业迎来转折", "source_id": "cls-hot"},
                {"title": "锂电池产业链供需紧张", "source_id": "wallstreetcn-hot"},
            ]
        )
        with patch.object(sentiment_data, "get_hot_news", return_value=news):
            with patch.object(sentiment_data, "insert_hot_keywords"), \
                patch.object(sentiment_data, "save_raw_payload"):
                payload = sentiment_data.get_hot_keywords()
        self.assertEqual("empty", payload["status"])
        self.assertEqual([], payload["data"])

    def test_skips_stopwords_when_aligned(self) -> None:
        # When stopwords appear as standalone tokens (separated by punctuation),
        # they are filtered. The test exercises that path explicitly.
        news = _make_news(
            [
                {"title": "财联社,新能源汽车,产业链", "source_id": "cls-hot"},
                {"title": "财联社,新能源汽车,产业链", "source_id": "wallstreetcn-hot"},
            ]
        )
        with patch.object(sentiment_data, "get_hot_news", return_value=news):
            with patch.object(sentiment_data, "insert_hot_keywords"), \
                patch.object(sentiment_data, "save_raw_payload"):
                payload = sentiment_data.get_hot_keywords()
        words = [item["word"] for item in payload["data"]]
        self.assertNotIn("财联社", words)
        self.assertIn("新能源汽车", words)


if __name__ == "__main__":
    unittest.main()
