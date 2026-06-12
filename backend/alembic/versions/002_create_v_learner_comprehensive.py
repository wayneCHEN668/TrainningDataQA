"""create_v_learner_comprehensive

Revision ID: 002
Create Date: 2026-06-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "v_learner_comprehensive",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(50), nullable=False),
        sa.Column("user_code", sa.String(30), nullable=True),
        sa.Column("user_name", sa.String(100), nullable=True),
        sa.Column("dept_code", sa.String(30), nullable=True),
        sa.Column("dept_name", sa.String(100), nullable=True),
        sa.Column("org_code", sa.String(30), nullable=True),
        sa.Column("class_code", sa.String(30), nullable=True),
        sa.Column("class_name", sa.String(100), nullable=True),
        sa.Column("total_courses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("courses_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_rate", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_composite_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("avg_courseware_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("avg_exam_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("avg_assignment_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("grade_rank", sa.String(10), nullable=True),
        sa.Column("total_exams_taken", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("exams_passed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("exam_pass_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("best_exam_score", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("total_study_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_study_sessions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_session_minutes", sa.Integer(), nullable=True),
        sa.Column("last_studied_at", sa.DateTime(), nullable=True),
        sa.Column("is_at_risk", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("risk_type", sa.String(50), nullable=True),
        sa.Column("days_since_last_study", sa.Integer(), nullable=True),
        sa.Column("refreshed_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uk_vlc"),
    )
    op.create_index("idx_vlc_dept", "v_learner_comprehensive", ["dept_code"])
    op.create_index("idx_vlc_org", "v_learner_comprehensive", ["org_code"])
    op.create_index("idx_vlc_risk", "v_learner_comprehensive", ["is_at_risk", "risk_type"])


def downgrade() -> None:
    op.drop_table("v_learner_comprehensive")
