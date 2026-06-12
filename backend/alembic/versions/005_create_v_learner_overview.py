"""create_v_learner_overview

Revision ID: 005
Create Date: 2026-06-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE VIEW v_learner_overview AS
        SELECT
            u.user_id, u.user_code, u.user_name, u.role_level,
            u.dept_code, d.dept_name,
            sc.class_code, cg.class_name,
            u.position_code, p.position_name,
            up.gender, up.education, up.job_title,
            up.last_login_at,
            d.org_code
        FROM user_info u
        LEFT JOIN department d ON u.dept_code = d.dept_code
        LEFT JOIN student_class sc ON u.user_id = sc.user_id
        LEFT JOIN class_group cg ON sc.class_code = cg.class_code
        LEFT JOIN position p ON u.position_code = p.position_code
        LEFT JOIN user_profile up ON u.user_id = up.user_id
        WHERE u.deleted_at IS NULL
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_learner_overview")
