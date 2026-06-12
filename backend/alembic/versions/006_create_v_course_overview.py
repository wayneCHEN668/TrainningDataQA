"""create_v_course_overview

Revision ID: 006
Create Date: 2026-06-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE VIEW v_course_overview AS
        SELECT
            c.course_code, c.course_name, c.credit, c.study_hours,
            c.category_code, cc.category_name,
            c.dept_code, d.dept_name,
            c.is_published,
            (SELECT COUNT(*) FROM course_courseware ccw
             WHERE ccw.course_code = c.course_code) AS courseware_count
        FROM course c
        LEFT JOIN course_category cc ON c.category_code = cc.category_code
        LEFT JOIN department d ON c.dept_code = d.dept_code
        WHERE c.deleted_at IS NULL
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_course_overview")
