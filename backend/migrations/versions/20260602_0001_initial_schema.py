"""Create the initial QuantDash data-center schema.

Revision ID: 20260602_0001
Revises:
Create Date: 2026-06-02
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260602_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "raw_payloads",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("dataset", sa.Text(), nullable=False),
        sa.Column("symbol", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "stock_profiles",
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("exchange", sa.Text(), nullable=False),
        sa.Column("industry", sa.Text(), nullable=True),
        sa.Column("listed_at", sa.Date(), nullable=True),
        sa.Column("delisted_at", sa.Date(), nullable=True),
        sa.Column("pinyin", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("symbol"),
    )
    op.create_table(
        "trade_calendar",
        sa.Column("exchange", sa.Text(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("is_open", sa.Boolean(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("exchange", "date"),
    )
    op.create_table(
        "daily_bars",
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("open", sa.Float(), nullable=True),
        sa.Column("high", sa.Float(), nullable=True),
        sa.Column("low", sa.Float(), nullable=True),
        sa.Column("close", sa.Float(), nullable=True),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("turnover", sa.Float(), nullable=True),
        sa.Column("amplitude", sa.Float(), nullable=True),
        sa.Column("change_rate", sa.Float(), nullable=True),
        sa.Column("change_amount", sa.Float(), nullable=True),
        sa.Column("turnover_rate", sa.Float(), nullable=True),
        sa.Column("adjust_type", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("symbol", "date", "adjust_type"),
    )
    op.create_table(
        "stock_status",
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("is_st", sa.Boolean(), nullable=False),
        sa.Column("is_suspended", sa.Boolean(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("symbol", "date"),
    )
    op.create_table(
        "limit_prices",
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("up_limit", sa.Float(), nullable=True),
        sa.Column("down_limit", sa.Float(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("symbol", "date"),
    )
    op.create_table(
        "financial_metrics",
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("report_period", sa.Text(), nullable=False),
        sa.Column("pe_ttm", sa.Float(), nullable=True),
        sa.Column("pb", sa.Float(), nullable=True),
        sa.Column("roe", sa.Float(), nullable=True),
        sa.Column("gross_margin", sa.Float(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("symbol", "report_period", "source"),
    )
    op.create_table(
        "hot_news_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.Text(), nullable=False),
        sa.Column("source_name", sa.Text(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "title", "captured_at"),
    )
    op.create_table(
        "news_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "hot_keywords",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("word", sa.Text(), nullable=False),
        sa.Column("heat", sa.Float(), nullable=True),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "data_jobs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("job_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "universes",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("base", sa.Text(), nullable=False),
        sa.Column("filters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "universe_members",
        sa.Column("universe_id", sa.Text(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("included", sa.Boolean(), nullable=False),
        sa.Column("excluded_reason", sa.Text(), nullable=True),
        sa.Column("can_buy", sa.Boolean(), nullable=False),
        sa.Column("can_sell", sa.Boolean(), nullable=False),
        sa.Column("flags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("universe_id", "date", "symbol"),
    )


def downgrade() -> None:
    op.drop_table("universe_members")
    op.drop_table("universes")
    op.drop_table("data_jobs")
    op.drop_table("hot_keywords")
    op.drop_table("news_items")
    op.drop_table("hot_news_items")
    op.drop_table("financial_metrics")
    op.drop_table("limit_prices")
    op.drop_table("stock_status")
    op.drop_table("daily_bars")
    op.drop_table("trade_calendar")
    op.drop_table("stock_profiles")
    op.drop_table("raw_payloads")
