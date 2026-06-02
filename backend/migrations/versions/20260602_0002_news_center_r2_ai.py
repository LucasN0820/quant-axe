"""Add News Center AI analysis persistence.

Revision ID: 20260602_0002
Revises: 20260602_0001
Create Date: 2026-06-02
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260602_0002"
down_revision: str | None = "20260602_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "hot_news_ai_analyses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("snapshot_key", sa.Text(), nullable=False),
        sa.Column("snapshot_etag", sa.Text(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("snapshot_crawl_time", sa.Text(), nullable=False),
        sa.Column("node_key", sa.Text(), nullable=False),
        sa.Column("analysis_mode", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("analyzed_news", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "hot_news_ai_analysis_runs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("execution_date", sa.Date(), nullable=False),
        sa.Column("node_key", sa.Text(), nullable=False),
        sa.Column("scheduled_time", sa.Text(), nullable=False),
        sa.Column("analysis_mode", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("snapshot_key", sa.Text(), nullable=True),
        sa.Column("snapshot_etag", sa.Text(), nullable=True),
        sa.Column("calendar_degraded", sa.Boolean(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("execution_date", "node_key", "scheduled_time"),
    )


def downgrade() -> None:
    op.drop_table("hot_news_ai_analysis_runs")
    op.drop_table("hot_news_ai_analyses")
