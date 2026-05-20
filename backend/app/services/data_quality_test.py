from __future__ import annotations

import unittest

from backend.app.services.data_quality import summarize_issues, validate_daily_bars


class DataQualityTest(unittest.TestCase):
    """Data quality rule tests."""

    def test_validate_daily_bars_accepts_well_formed_rows(self) -> None:
        rows = [
            {
                "date": "2026-05-18",
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 1000,
                "turnover": 10200,
                "change_rate": 1.2,
            }
        ]

        issues = validate_daily_bars(rows, open_dates={"2026-05-18"})

        self.assertEqual([], issues)

    def test_validate_daily_bars_reports_duplicate_and_shape_errors(self) -> None:
        rows = [
            {
                "date": "2026-05-18",
                "open": 11.0,
                "high": 10.0,
                "low": 10.5,
                "close": 9.0,
                "volume": -1,
                "turnover": -2,
                "change_rate": 35.0,
            },
            {
                "date": "2026-05-18",
                "open": 10.0,
                "high": 10.2,
                "low": 9.8,
                "close": 10.1,
                "volume": 100,
            },
        ]

        summary = summarize_issues(validate_daily_bars(rows, open_dates={"2026-05-18"}))
        codes = {issue["code"] for issue in summary["issues"]}

        self.assertIn("duplicate_trade_date", codes)
        self.assertIn("invalid_high_low", codes)
        self.assertIn("negative_volume", codes)
        self.assertIn("negative_turnover", codes)
        self.assertIn("abnormal_change_rate", codes)


if __name__ == "__main__":
    unittest.main()
