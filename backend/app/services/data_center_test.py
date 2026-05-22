from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.app.services import data_center
from backend.app.services.data_center import (
    get_served_quotes,
    infer_exchange,
    limit_ratio,
    normalize_provider_date,
    normalize_symbol_list,
)


class DataCenterTest(unittest.TestCase):
    """Data Center helper tests."""

    def setUp(self) -> None:
        data_center.RUNTIME_CACHE.clear()

    def test_infer_exchange_from_a_share_symbol(self) -> None:
        self.assertEqual("SSE", infer_exchange("600519"))
        self.assertEqual("SZSE", infer_exchange("000001"))
        self.assertEqual("SZSE", infer_exchange("300750"))
        self.assertEqual("BSE", infer_exchange("830799"))

    def test_limit_ratio_uses_st_and_board_rules(self) -> None:
        self.assertEqual(0.05, limit_ratio("600000", "ST Test"))
        self.assertEqual(0.20, limit_ratio("300750", "宁德时代"))
        self.assertEqual(0.20, limit_ratio("688001", "华兴源创"))
        self.assertEqual(0.10, limit_ratio("600519", "贵州茅台"))

    def test_normalize_provider_date(self) -> None:
        self.assertEqual("2026-05-18", normalize_provider_date("20260518"))
        self.assertEqual("2026-05-18", normalize_provider_date("2026-05-18T00:00:00"))
        self.assertIsNone(normalize_provider_date(""))

    def test_normalize_symbol_list_dedupes_and_validates(self) -> None:
        self.assertEqual(["600519", "300750"], normalize_symbol_list("600519, sh300750,600519"))
        with self.assertRaises(ValueError):
            normalize_symbol_list("abc")

    def test_get_served_quotes_uses_cache_and_fetches_misses(self) -> None:
        def cache_get(key: str):
            if key == "quote:600519":
                return {"symbol": "600519", "name": "贵州茅台"}
            return None

        def quote(symbol: str):
            return {"symbol": symbol, "name": "宁德时代"}

        with patch.object(data_center, "cache_get_json", side_effect=cache_get), \
            patch.object(data_center, "cache_set_json") as cache_set, \
            patch.object(data_center, "get_quote", side_effect=quote):
            payload = get_served_quotes("600519,300750")

        self.assertEqual("ready", payload["status"])
        self.assertEqual(["600519", "300750"], [row["symbol"] for row in payload["data"]])
        self.assertEqual({"hits": 1, "misses": 1}, payload["cache"])
        cache_set.assert_called_once()


if __name__ == "__main__":
    unittest.main()
