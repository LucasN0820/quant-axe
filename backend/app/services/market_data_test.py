from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.app.services import market_data


class FakeFrame:
    """Minimal pandas-like frame used by provider adapter tests."""

    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    def to_dict(self, _orient: str) -> list[dict]:
        return self.rows


class FakeResponse:
    """Minimal requests-like response containing one Sina quote."""

    text = (
        'var hq_str_sz300750="宁德时代,423.000,415.680,424.000,430.860,416.550,'
        "423.990,424.000,49811891,21139031903.920,2500,423.990,4000,423.980,"
        "1400,423.970,1500,423.960,100,423.950,70763,424.000,1200,424.010,"
        '300,424.020,200,424.030,100,424.040,2026-05-29,15:35:30,00,";'
    )
    encoding = ""

    @staticmethod
    def raise_for_status() -> None:
        return None


class FakeAkshare:
    """AkShare double with an unavailable Eastmoney index endpoint."""

    @staticmethod
    def stock_zh_index_spot_em(**_kwargs):
        raise ConnectionError("eastmoney unavailable")

    @staticmethod
    def stock_zh_index_spot_sina():
        return FakeFrame(
            [
                {
                    "代码": "sh000001",
                    "名称": "上证指数",
                    "最新价": 4068.57,
                    "涨跌额": -30.07,
                    "涨跌幅": -0.73,
                    "成交量": 731597710,
                    "成交额": 1532067352982,
                }
            ]
        )


class MarketDataTest(unittest.TestCase):
    """Real-time provider fallback tests."""

    def test_sina_quote_map_parses_prices_and_order_book(self) -> None:
        with patch.object(market_data.requests, "get", return_value=FakeResponse()):
            quote = market_data.sina_quote_map("300750")

        self.assertEqual("宁德时代", quote["股票简称"])
        self.assertEqual("424.000", quote["最新"])
        self.assertEqual("423.990", quote["buy_1"])
        self.assertEqual("70763", quote["sell_1_vol"])

    def test_get_quote_falls_back_to_sina(self) -> None:
        with patch.object(market_data, "bid_ask_map", side_effect=ConnectionError), \
            patch.object(market_data, "sina_quote_map") as sina_quote:
            sina_quote.return_value = {
                "股票简称": "宁德时代",
                "今开": "423.000",
                "昨收": "415.680",
                "最新": "424.000",
                "最高": "430.860",
                "最低": "416.550",
                "金额": "21139031903.920",
                "总手": "49811891",
                "交易日期": "2026-05-29",
                "交易时间": "15:35:30",
            }
            payload = market_data.get_quote("300750")

        self.assertEqual("宁德时代", payload["name"])
        self.assertEqual(424.0, payload["current_price"])
        self.assertEqual(2.0, payload["change_rate"])
        self.assertEqual("sina.hq", payload["source"])

    def test_get_indexes_falls_back_to_sina(self) -> None:
        with patch.object(market_data, "load_akshare", return_value=FakeAkshare()):
            payload = market_data.get_indexes()

        self.assertEqual("akshare.stock_zh_index_spot_sina", payload["source"])
        self.assertEqual("000001", payload["data"][0]["symbol"])
        self.assertEqual(4068.57, payload["data"][0]["value"])


if __name__ == "__main__":
    unittest.main()
