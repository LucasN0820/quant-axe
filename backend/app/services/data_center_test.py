from __future__ import annotations

import unittest

from backend.app.services.data_center import infer_exchange, limit_ratio, normalize_provider_date


class DataCenterTest(unittest.TestCase):
    """Data Center helper tests."""

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


if __name__ == "__main__":
    unittest.main()
