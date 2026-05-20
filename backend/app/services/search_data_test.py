from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.app.services import search_data


SAMPLE_INDEX = (
    {
        "kind": "stock",
        "symbol": "600519",
        "name": "贵州茅台",
        "exchange": "SSE",
        "pinyin": "guizhoumaotai",
        "pinyin_initial": "gzmt",
    },
    {
        "kind": "stock",
        "symbol": "300750",
        "name": "宁德时代",
        "exchange": "SZSE",
        "pinyin": "ningdeshidai",
        "pinyin_initial": "ndsd",
    },
    {
        "kind": "index",
        "symbol": "000300",
        "name": "沪深300",
        "exchange": "SSE",
        "pinyin": "hushen300",
        "pinyin_initial": "hs",
    },
    {
        "kind": "etf",
        "symbol": "510050",
        "name": "上证50ETF",
        "exchange": "SSE",
        "pinyin": "shangzheng50etf",
        "pinyin_initial": "sz50etf",
    },
    {
        "kind": "stock",
        "symbol": "830799",
        "name": "爱迪特",
        "exchange": "BSE",
        "pinyin": "aidite",
        "pinyin_initial": "adt",
    },
)


class SearchDataTest(unittest.TestCase):
    """Cross-asset search index tests."""

    def setUp(self) -> None:
        search_data.search_index.cache_clear()

    def test_matches_by_full_symbol(self) -> None:
        with patch.object(search_data, "search_index", return_value=SAMPLE_INDEX):
            payload = search_data.search_universe("600519")
        self.assertEqual("600519", payload["data"][0]["symbol"])

    def test_matches_by_chinese_name_substring(self) -> None:
        with patch.object(search_data, "search_index", return_value=SAMPLE_INDEX):
            payload = search_data.search_universe("茅台")
        self.assertTrue(any(row["symbol"] == "600519" for row in payload["data"]))

    def test_matches_by_pinyin_initial(self) -> None:
        with patch.object(search_data, "search_index", return_value=SAMPLE_INDEX):
            payload = search_data.search_universe("ndsd")
        self.assertEqual("300750", payload["data"][0]["symbol"])

    def test_includes_indexes_and_etfs(self) -> None:
        with patch.object(search_data, "search_index", return_value=SAMPLE_INDEX):
            index_payload = search_data.search_universe("沪深")
            etf_payload = search_data.search_universe("ETF")
        self.assertTrue(any(row["kind"] == "index" for row in index_payload["data"]))
        self.assertTrue(any(row["kind"] == "etf" for row in etf_payload["data"]))

    def test_includes_bse_symbols(self) -> None:
        with patch.object(search_data, "search_index", return_value=SAMPLE_INDEX):
            payload = search_data.search_universe("830799")
        self.assertEqual("BSE", payload["data"][0]["exchange"])


if __name__ == "__main__":
    unittest.main()
