from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.app.services import search_data


class FakeFrame:
    """Minimal pandas-like frame used by provider adapter tests."""

    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    def to_dict(self, _orient: str) -> list[dict]:
        return self.rows


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

    def test_search_index_uses_persistent_cache(self) -> None:
        with patch.object(search_data, "cache_get_json", return_value=list(SAMPLE_INDEX)), \
            patch.object(search_data, "load_a_share_universe") as load_stocks:
            rows = search_data.search_index()
        self.assertEqual(SAMPLE_INDEX, rows)
        load_stocks.assert_not_called()

    def test_search_index_uses_stale_cache_when_provider_returns_partial_data(self) -> None:
        partial = [SAMPLE_INDEX[-1]]

        def cache_get(key: str):
            if key == search_data.SEARCH_INDEX_STALE_CACHE_KEY:
                return list(SAMPLE_INDEX)
            return None

        with patch.object(search_data, "cache_get_json", side_effect=cache_get), \
            patch.object(search_data, "load_a_share_universe", return_value=partial), \
            patch.object(search_data, "load_index_universe", return_value=[]), \
            patch.object(search_data, "load_etf_universe", return_value=[]):
            rows = search_data.search_index()
        self.assertEqual(SAMPLE_INDEX, rows)

    def test_load_index_universe_falls_back_to_sina(self) -> None:
        class FakeAkshare:
            """AkShare double with only the Sina index endpoint available."""

            @staticmethod
            def stock_zh_index_spot_em(**_kwargs):
                raise ConnectionError("eastmoney unavailable")

            @staticmethod
            def stock_zh_index_spot_sina():
                return FakeFrame([{"代码": "sh000001", "名称": "上证指数"}])

        with patch.object(search_data, "load_akshare", return_value=FakeAkshare()):
            rows = search_data.load_index_universe()
        self.assertEqual("000001", rows[0]["symbol"])

    def test_load_etf_universe_uses_fast_ths_source(self) -> None:
        class FakeAkshare:
            """AkShare double exposing the fast ETF directory."""

            @staticmethod
            def fund_etf_spot_ths():
                return FakeFrame([{"基金代码": "510050", "基金名称": "上证50ETF"}])

        with patch.object(search_data, "load_akshare", return_value=FakeAkshare()):
            rows = search_data.load_etf_universe()
        self.assertEqual("510050", rows[0]["symbol"])


if __name__ == "__main__":
    unittest.main()
