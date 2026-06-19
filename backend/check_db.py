import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as s:
        tables = [
            ("department", "SELECT COUNT(*) as cnt FROM department"),
            ("user_info", "SELECT COUNT(*) as cnt FROM user_info"),
            ("course", "SELECT COUNT(*) as cnt FROM course"),
            ("course_grade", "SELECT COUNT(*) as cnt FROM course_grade"),
            ("learning_progress", "SELECT COUNT(*) as cnt FROM learning_progress"),
            ("exam_session", "SELECT COUNT(*) as cnt FROM exam_session"),
            ("exam_enrollment", "SELECT COUNT(*) as cnt FROM exam_enrollment"),
            ("class_info", "SELECT COUNT(*) as cnt FROM class_info"),
            ("student_class", "SELECT COUNT(*) as cnt FROM student_class"),
            ("v_learner_comprehensive", "SELECT COUNT(*) as cnt FROM v_learner_comprehensive"),
            ("v_exam_analysis", "SELECT COUNT(*) as cnt FROM v_exam_analysis"),
            ("v_skill_error_summary", "SELECT COUNT(*) as cnt FROM v_skill_error_summary"),
            ("dept_benchmark_stats", "SELECT COUNT(*) as cnt FROM dept_benchmark_stats"),
            ("org_benchmark_stats", "SELECT COUNT(*) as cnt FROM org_benchmark_stats"),
            ("org_daily_stats", "SELECT COUNT(*) as cnt FROM org_daily_stats"),
            ("study_session_log", "SELECT COUNT(*) as cnt FROM study_session_log"),
        ]
        for name, sql in tables:
            try:
                r = await s.execute(text(sql))
                row = r.mappings().first()
                print(f"{name}: {row['cnt']} rows")
            except Exception as e:
                print(f"{name}: ERROR - {e}")

        # Check user_info sample
        print("\n=== user_info sample ===")
        r = await s.execute(text("SELECT user_id, user_code, user_name, dept_code, role_level FROM user_info LIMIT 5"))
        for row in r.mappings():
            print(dict(row))

        # Check course sample
        print("\n=== course sample ===")
        r = await s.execute(text("SELECT course_code, course_name, dept_code FROM course LIMIT 5"))
        for row in r.mappings():
            print(dict(row))

        # Check course_grade with dept info
        print("\n=== course_grade + user_info + department ===")
        r = await s.execute(text("""
            SELECT cg.user_id, ui.user_name, d.dept_name, cg.completion_rate, cg.total_score, cg.is_passed
            FROM course_grade cg
            LEFT JOIN user_info ui ON cg.user_id = ui.user_id
            LEFT JOIN department d ON ui.dept_code = d.dept_code
            LIMIT 10
        """))
        for row in r.mappings():
            print(dict(row))

asyncio.run(main())