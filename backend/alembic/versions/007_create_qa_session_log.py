"""create_qa_session_log

Revision ID: 007
Create Date: 2026-06-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "qa_session_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(50), nullable=False),
        sa.Column("user_id", sa.String(50), nullable=False),
        sa.Column("org_code", sa.String(30), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(50), nullable=True),
        sa.Column("complexity", sa.String(10), nullable=True),
        sa.Column("modules_used", sa.String(300), nullable=True),
        sa.Column("steps_count", sa.Integer(), server_default="0"),
        sa.Column("tools_used", sa.String(300), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("user_feedback", sa.SmallInteger(), nullable=True),
        sa.Column("fallback_used", sa.Boolean(), server_default="0"),
        sa.Column("asked_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_qsl_asked", "qa_session_log", ["asked_at"])
    op.create_index("idx_qsl_intent", "qa_session_log", ["intent"])
    op.create_index("idx_qsl_feedback", "qa_session_log", ["user_feedback"])


def downgrade() -> None:
    op.drop_table("qa_session_log")
