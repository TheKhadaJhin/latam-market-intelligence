"""Create the market intelligence schema.

Revision ID: 20260827_0001
Revises:
Create Date: 2026-08-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260827_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "countries",
        sa.Column("code", sa.String(length=3), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "indicators",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("unit", sa.String(length=80), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("polarity", sa.String(length=16), nullable=False),
        sa.Column("base_weight", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "observations",
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("indicator_code", sa.String(length=64), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("source_updated_at", sa.String(length=32), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["country_code"], ["countries.code"]),
        sa.ForeignKeyConstraint(["indicator_code"], ["indicators.code"]),
        sa.PrimaryKeyConstraint("country_code", "indicator_code", "year"),
    )
    op.create_table(
        "market_scores",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("reference_year", sa.Integer(), nullable=False),
        sa.Column("scenario", sa.String(length=24), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("coverage_ratio", sa.Float(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("dimensions_json", sa.Text(), nullable=False),
        sa.Column("indicator_scores_json", sa.Text(), nullable=False),
        sa.Column("indicator_years_json", sa.Text(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["country_code"], ["countries.code"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("country_code", "reference_year", "scenario", name="uq_market_score"),
    )
    op.create_index("ix_market_scores_country_code", "market_scores", ["country_code"])
    op.create_index("ix_market_scores_reference_year", "market_scores", ["reference_year"])
    op.create_index("ix_market_scores_scenario", "market_scores", ["scenario"])
    op.create_table(
        "pipeline_runs",
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("records_received", sa.Integer(), nullable=False),
        sa.Column("records_upserted", sa.Integer(), nullable=False),
        sa.Column("rankings_calculated", sa.Integer(), nullable=False),
        sa.Column("reference_year", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_updated_at", sa.String(length=32), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("run_id"),
    )
    op.create_index("ix_pipeline_runs_status", "pipeline_runs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_pipeline_runs_status", table_name="pipeline_runs")
    op.drop_table("pipeline_runs")
    op.drop_index("ix_market_scores_scenario", table_name="market_scores")
    op.drop_index("ix_market_scores_reference_year", table_name="market_scores")
    op.drop_index("ix_market_scores_country_code", table_name="market_scores")
    op.drop_table("market_scores")
    op.drop_table("observations")
    op.drop_table("indicators")
    op.drop_table("countries")
