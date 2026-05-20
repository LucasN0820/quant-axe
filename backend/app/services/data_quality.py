"""Data quality checks for clean and serving market datasets."""
# pylint: disable=duplicate-code

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class QualityIssue:
    """One data quality problem found in a checked dataset."""

    code: str
    severity: str
    message: str
    row_ref: str | None = None


REQUIRED_DAILY_BAR_FIELDS = ("date", "open", "high", "low", "close", "volume")


def validate_daily_bars(
    rows: Iterable[dict[str, Any]],
    *,
    open_dates: set[str] | None = None,
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    seen_dates: set[str] = set()

    for row in rows:
        row_date = stringify(row.get("date"))
        row_ref = row_date or None
        if not row_date:
            issues.append(QualityIssue("missing_date", "error", "daily bar has no date"))
            continue

        if row_date in seen_dates:
            issues.append(
                QualityIssue("duplicate_trade_date", "error", "duplicate daily bar date", row_ref)
            )
        seen_dates.add(row_date)

        if open_dates is not None and row_date not in open_dates:
            issues.append(
                QualityIssue(
                    "non_trading_day_bar",
                    "warning",
                    "daily bar appears on a non-open calendar date",
                    row_ref,
                )
            )

        for field in REQUIRED_DAILY_BAR_FIELDS:
            if row.get(field) is None:
                issues.append(
                    QualityIssue("missing_required_value", "error", f"missing {field}", row_ref)
                )

        check_price_shape(row, issues, row_ref)
        check_return_shape(row, issues, row_ref)

    return issues


def check_price_shape(
    row: dict[str, Any],
    issues: list[QualityIssue],
    row_ref: str | None,
) -> None:
    high = to_float(row.get("high"))
    low = to_float(row.get("low"))
    open_price = to_float(row.get("open"))
    close = to_float(row.get("close"))
    prices = [value for value in (open_price, high, low, close) if value is not None]

    if any(value <= 0 for value in prices):
        issues.append(
            QualityIssue("non_positive_price", "error", "price must be positive", row_ref)
        )

    if high is not None and low is not None and high < low:
        issues.append(QualityIssue("invalid_high_low", "error", "high is lower than low", row_ref))

    if high is not None and low is not None:
        for field_name, value in (("open", open_price), ("close", close)):
            if value is not None and not low <= value <= high:
                issues.append(
                    QualityIssue(
                        "price_outside_range",
                        "error",
                        f"{field_name} is outside low/high range",
                        row_ref,
                    )
                )


def check_return_shape(
    row: dict[str, Any],
    issues: list[QualityIssue],
    row_ref: str | None,
) -> None:
    change_rate = to_float(row.get("change_rate"))
    if change_rate is not None and abs(change_rate) > 30:
        issues.append(
            QualityIssue(
                "abnormal_change_rate",
                "warning",
                "daily change rate exceeds broad A-share limit expectations",
                row_ref,
            )
        )

    volume = to_float(row.get("volume"))
    if volume is not None and volume < 0:
        issues.append(
            QualityIssue("negative_volume", "error", "volume must not be negative", row_ref)
        )

    turnover = to_float(row.get("turnover"))
    if turnover is not None and turnover < 0:
        issues.append(
            QualityIssue("negative_turnover", "error", "turnover must not be negative", row_ref)
        )


def summarize_issues(issues: list[QualityIssue]) -> dict[str, Any]:
    return {
        "total": len(issues),
        "errors": sum(1 for issue in issues if issue.severity == "error"),
        "warnings": sum(1 for issue in issues if issue.severity == "warning"),
        "issues": [issue.__dict__ for issue in issues],
    }


def open_date_set(calendar_rows: Iterable[dict[str, Any]]) -> set[str]:
    return {stringify(row.get("date")) for row in calendar_rows if row.get("is_open") is True}


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
