from __future__ import annotations

import unittest

from backend.app.services.intraday_data import format_time, normalize_side


class IntradayDataTest(unittest.TestCase):
    """Intraday/trade-print helper tests."""

    def test_normalize_side_chinese_aliases(self) -> None:
        self.assertEqual("买入", normalize_side("买"))
        self.assertEqual("买入", normalize_side("主买"))
        self.assertEqual("卖出", normalize_side("卖"))
        self.assertEqual("卖出", normalize_side("主卖"))
        self.assertEqual("中性", normalize_side(""))

    def test_format_time_strips_date_part(self) -> None:
        self.assertEqual("09:30:00", format_time("2026-05-18 09:30:00"))
        self.assertEqual("09:30:00", format_time("2026-05-18T09:30:00"))
        self.assertEqual("09:30:00", format_time("09:30:00"))


if __name__ == "__main__":
    unittest.main()
