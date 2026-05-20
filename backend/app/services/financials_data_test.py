from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.app.services import financials_data


class FinancialsDataTest(unittest.TestCase):
    """Tushare financial metrics merging tests."""

    def test_returns_not_configured_when_token_missing(self) -> None:
        with patch.object(financials_data, "TUSHARE_TOKEN", ""):
            payload = financials_data.get_financial_metrics("600519")
        self.assertEqual("not_configured", payload["status"])
        self.assertEqual("600519", payload["symbol"])

    def test_merges_daily_basic_and_fina_indicator(self) -> None:
        daily = {
            "symbol": "600519",
            "source": "tushare.daily_basic",
            "status": "ready",
            "data": {
                "trade_date": "2026-05-18",
                "close": 1700.0,
                "pe": 30.1,
                "pe_ttm": 28.5,
                "pb": 9.1,
                "ps_ttm": 11.2,
                "dv_ttm": 1.8,
                "turnover_rate": 0.4,
                "turnover_rate_f": 0.5,
                "total_mv": 21000000.0,
                "circ_mv": 21000000.0,
                "total_share": 1256.0,
                "float_share": 1256.0,
            },
        }
        indicator = {
            "symbol": "600519",
            "source": "tushare.fina_indicator",
            "status": "ready",
            "data": {
                "report_period": "2026-03-31",
                "roe": 33.0,
                "roe_waa": 32.5,
                "roe_dt": 31.0,
                "gross_margin": 91.5,
                "netprofit_margin": 51.0,
                "debt_to_assets": 17.0,
                "revenue_yoy": 18.5,
                "netprofit_yoy": 19.0,
                "assets_yoy": 12.0,
            },
        }

        def fake_safe_fetch(_symbol: str, dataset: str):
            return daily if dataset == "daily_basic" else indicator

        with patch.object(financials_data, "TUSHARE_TOKEN", "x"), \
            patch.object(financials_data, "safe_fetch", side_effect=fake_safe_fetch), \
            patch.object(financials_data, "upsert_financial_metrics"), \
            patch.object(financials_data, "save_raw_payload"):
            payload = financials_data.get_financial_metrics("600519")

        self.assertEqual("ready", payload["status"])
        data = payload["data"]
        self.assertEqual(28.5, data["pe_ttm"])
        self.assertEqual(33.0, data["roe"])
        self.assertEqual(91.5, data["gross_margin"])
        self.assertEqual("2026-03-31", data["report_period"])

    def test_handles_partial_provider_failures(self) -> None:
        daily = {
            "symbol": "600519",
            "source": "tushare.daily_basic",
            "status": "ready",
            "data": {"trade_date": "2026-05-18", "pe_ttm": 25.0, "pb": 8.0},
        }
        indicator = {
            "symbol": "600519",
            "source": "tushare.fina_indicator",
            "status": "unavailable",
            "data": None,
        }

        def fake_safe_fetch(_symbol: str, dataset: str):
            return daily if dataset == "daily_basic" else indicator

        with patch.object(financials_data, "TUSHARE_TOKEN", "x"), \
            patch.object(financials_data, "safe_fetch", side_effect=fake_safe_fetch), \
            patch.object(financials_data, "upsert_financial_metrics"), \
            patch.object(financials_data, "save_raw_payload"):
            payload = financials_data.get_financial_metrics("600519")

        self.assertEqual("ready", payload["status"])
        self.assertEqual(25.0, payload["data"]["pe_ttm"])
        self.assertIsNone(payload["data"]["roe"])
        self.assertEqual("unavailable", payload["providers"]["fina_indicator"])


if __name__ == "__main__":
    unittest.main()
