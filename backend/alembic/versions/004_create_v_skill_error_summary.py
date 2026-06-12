"""create_v_skill_error_summary

Revision ID: 004
Create Date: 2026-06-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "v_skill_error_summary",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("courseware_code", sa.String(30), nullable=False),
        sa.Column("courseware_name", sa.String(100), nullable=True),
        sa.Column("course_code", sa.String(30), nullable=True),
        sa.Column("dept_code", sa.String(30), nullable=True),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("total_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_errors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_rate", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("unique_users", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_errors_per_user", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("stat_date", sa.Date(), nullable=False),
        sa.Column("refreshed_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_vses_courseware", "v_skill_error_summary", ["courseware_code"])
    op.create_index("idx_vses_course", "v_skill_error_summary", ["course_code"])
    op.create_index("idx_vses_dept", "v_skill_error_summary", ["dept_code"])
    op.create_index("idx_vses_date", "v_skill_error_summary", ["stat_date"])


def downgrade() -> None:
    op.drop_table("v_skill_error_summary")
