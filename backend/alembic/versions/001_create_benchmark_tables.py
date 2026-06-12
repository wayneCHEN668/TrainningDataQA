"""create_benchmark_tables

Revision ID: 001
Create Date: 2026-06-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dept_benchmark_stats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("dept_code", sa.String(30), nullable=False),
        sa.Column("org_code", sa.String(30), nullable=False),
        sa.Column("stat_period", sa.String(10), nullable=False, server_default="month"),
        sa.Column("stat_date", sa.Date(), nullable=False),
        sa.Column("avg_completion_rate", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_exam_pass_rate", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_composite_score", sa.DECIMAL(6, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_study_minutes", sa.DECIMAL(10, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_skill_error_rate", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_engagement_score", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("p25_completion_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("p50_completion_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("p75_completion_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("p25_composite_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("p50_composite_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("p75_composite_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("total_learners", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("refreshed_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dept_code", "stat_period", "stat_date", name="uk_dbs"),
    )
    op.create_index("idx_dbs_org", "dept_benchmark_stats", ["org_code"])
    op.create_index("idx_dbs_date", "dept_benchmark_stats", ["stat_date"])

    op.create_table(
        "org_benchmark_stats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("org_code", sa.String(30), nullable=False),
        sa.Column("stat_period", sa.String(10), nullable=False, server_default="month"),
        sa.Column("stat_date", sa.Date(), nullable=False),
        sa.Column("avg_completion_rate", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_exam_pass_rate", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_composite_score", sa.DECIMAL(6, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_study_minutes", sa.DECIMAL(10, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_skill_error_rate", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_engagement_score", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("p25_completion_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("p50_completion_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("p75_completion_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("p25_composite_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("p50_composite_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("p75_composite_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("total_orgs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_learners", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("refreshed_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("org_code", "stat_period", "stat_date", name="uk_obs"),
    )
    op.create_index("idx_obs_date", "org_benchmark_stats", ["stat_date"])


def downgrade() -> None:
    op.drop_table("org_benchmark_stats")
    op.drop_table("dept_benchmark_stats")
