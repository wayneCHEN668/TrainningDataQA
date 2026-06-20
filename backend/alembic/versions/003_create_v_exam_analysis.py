"""create_v_exam_analysis

Revision ID: 003
Create Date: 2026-06-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "v_exam_analysis",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("exam_session_code", sa.String(30), nullable=False),
        sa.Column("session_name", sa.String(200), nullable=True),
        sa.Column("open_at", sa.DateTime(), nullable=True),
        sa.Column("close_at", sa.DateTime(), nullable=True),
        sa.Column("linked_course_code", sa.String(30), nullable=True),
        sa.Column("user_code", sa.String(30), nullable=False),
        sa.Column("user_id", sa.String(50), nullable=True),
        sa.Column("dept_code", sa.String(30), nullable=True),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_score", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("is_passed", sa.Boolean(), nullable=True),
        sa.Column("is_graded", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("type_scores", sa.JSON(), nullable=True),
        sa.Column("correct_count", sa.Integer(), nullable=True),
        sa.Column("total_questions", sa.Integer(), nullable=True),
        sa.Column("accuracy_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("refreshed_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_vea_session", "v_exam_analysis", ["exam_session_code"])
    op.create_index("idx_vea_user", "v_exam_analysis", ["user_code"])
    op.create_index("idx_vea_course", "v_exam_analysis", ["linked_course_code"])
    op.create_index("idx_vea_open_at", "v_exam_analysis", ["open_at"])


def downgrade() -> None:
    op.drop_table("v_exam_analysis")
