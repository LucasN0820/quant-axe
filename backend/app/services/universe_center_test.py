from __future__ import annotations

import unittest

from backend.app.services.universe_center import (
    FilterContext,
    apply_filter_pipeline,
    normalize_universe_payload,
)


class UniverseCenterTest(unittest.TestCase):
    """Universe Center filter pipeline tests."""

    def test_st_and_suspension_filters_keep_first_exclusion_reason(self) -> None:
        candidates = [
            {"symbol": "600001", "name": "正常股票", "listed_at": "2020-01-01"},
            {"symbol": "600002", "name": "ST股票", "listed_at": "2020-01-01"},
            {"symbol": "600003", "name": "停牌股票", "listed_at": "2020-01-01"},
        ]
        context = FilterContext(
            target_date="2026-05-20",
            status_by_symbol={
                "600002": {"is_st": True, "is_suspended": True},
                "600003": {"is_st": False, "is_suspended": True},
            },
        )

        members = apply_filter_pipeline(
            candidates,
            [{"type": "st"}, {"type": "suspension"}],
            context,
        )

        by_symbol = {row["symbol"]: row for row in members}
        self.assertTrue(by_symbol["600001"]["included"])
        self.assertFalse(by_symbol["600002"]["included"])
        self.assertEqual("ST", by_symbol["600002"]["excluded_reason"])
        self.assertFalse(by_symbol["600003"]["included"])
        self.assertEqual("停牌", by_symbol["600003"]["excluded_reason"])

    def test_listed_days_liquidity_and_price_filters(self) -> None:
        candidates = [
            {"symbol": "600001", "name": "新股", "listed_at": "2026-05-01"},
            {"symbol": "600002", "name": "低流动性", "listed_at": "2020-01-01"},
            {"symbol": "600003", "name": "高价股", "listed_at": "2020-01-01"},
            {"symbol": "600004", "name": "通过", "listed_at": "2020-01-01"},
        ]
        context = FilterContext(
            target_date="2026-05-20",
            daily_bar_by_symbol={
                "600002": {"turnover": 50_000_000, "close": 20},
                "600003": {"turnover": 200_000_000, "close": 120},
                "600004": {"turnover": 200_000_000, "close": 30},
            },
        )

        members = apply_filter_pipeline(
            candidates,
            [
                {"type": "listed_days", "min_days": 60},
                {"type": "liquidity", "min_turnover": 100_000_000},
                {"type": "price", "min_price": 5, "max_price": 80},
            ],
            context,
        )

        by_symbol = {row["symbol"]: row for row in members}
        self.assertEqual("上市不足60天", by_symbol["600001"]["excluded_reason"])
        self.assertEqual("成交额低于100000000", by_symbol["600002"]["excluded_reason"])
        self.assertEqual("价格高于80", by_symbol["600003"]["excluded_reason"])
        self.assertTrue(by_symbol["600004"]["included"])

    def test_limit_up_down_filter_marks_trading_state_without_excluding(self) -> None:
        candidates = [
            {"symbol": "600001", "name": "涨停", "listed_at": "2020-01-01"},
            {"symbol": "600002", "name": "跌停", "listed_at": "2020-01-01"},
        ]
        context = FilterContext(
            target_date="2026-05-20",
            daily_bar_by_symbol={
                "600001": {"close": 11},
                "600002": {"close": 9},
            },
            limit_price_by_symbol={
                "600001": {"up_limit": 11, "down_limit": 9},
                "600002": {"up_limit": 11, "down_limit": 9},
            },
        )

        members = apply_filter_pipeline(candidates, [{"type": "limit_up_down"}], context)

        by_symbol = {row["symbol"]: row for row in members}
        self.assertTrue(by_symbol["600001"]["included"])
        self.assertFalse(by_symbol["600001"]["can_buy"])
        self.assertIn("limit_up", by_symbol["600001"]["flags"])
        self.assertTrue(by_symbol["600002"]["included"])
        self.assertFalse(by_symbol["600002"]["can_sell"])
        self.assertIn("limit_down", by_symbol["600002"]["flags"])

    def test_universe_payload_validation(self) -> None:
        universe = normalize_universe_payload(
            {
                "name": "测试池",
                "base": "hs300",
                "filters": [{"type": "st"}, {"type": "suspension"}],
            },
            created_at="2026-05-20T00:00:00+00:00",
            updated_at="2026-05-20T00:00:00+00:00",
        )

        self.assertEqual("测试池", universe["name"])
        self.assertEqual("hs300", universe["base"])

        with self.assertRaises(ValueError):
            normalize_universe_payload(
                {"base": "unknown"},
                created_at="2026-05-20T00:00:00+00:00",
                updated_at="2026-05-20T00:00:00+00:00",
            )


if __name__ == "__main__":
    unittest.main()
