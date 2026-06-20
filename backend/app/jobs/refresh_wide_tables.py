"""宽表和基准表的定时刷新逻辑。"""
import logging
from datetime import date, timedelta

from sqlalchemy import text
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def _execute_refresh(table_name: str, sql: str) -> None:
    """通用刷新：执行给定的刷新 SQL。"""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(text(sql))
            await session.commit()
            logger.info("%s 刷新完成，影响行数: %s", table_name, result.rowcount)
        except Exception:
            await session.rollback()
            logger.exception("%s 刷新失败", table_name)
            raise


async def refresh_benchmark_stats() -> None:
    """每月 1 日 04:00 执行：重建上月院系/机构基准统计。"""
    today = date.today()
    first_of_month = today.replace(day=1)
    last_month_end = first_of_month - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    sql = f"""
        -- dept 级基准（简化版，实际生产需加分位数计算）
        INSERT INTO dept_benchmark_stats
            (dept_code, org_code, stat_period, stat_date,
             avg_completion_rate, avg_composite_score, total_learners)
        SELECT
            d.dept_code, d.org_code, 'month', '{last_month_end}',
            COALESCE(AVG(cg.completion_rate), 0),
            COALESCE(AVG(cg.total_score), 0),
            COUNT(DISTINCT u.user_id)
        FROM department d
        JOIN user_info u ON u.dept_code = d.dept_code AND u.deleted_at IS NULL
        LEFT JOIN course_grade cg ON u.user_id = cg.user_id
        WHERE u.role_level = 3
        GROUP BY d.dept_code, d.org_code
        ON DUPLICATE KEY UPDATE
            avg_completion_rate = VALUES(avg_completion_rate),
            avg_composite_score = VALUES(avg_composite_score),
            total_learners = VALUES(total_learners),
            refreshed_at = CURRENT_TIMESTAMP
    """
    await _execute_refresh("dept_benchmark_stats", sql)

    # org 级基准（同理，按 org_code GROUP BY）
    sql_org = f"""
        INSERT INTO org_benchmark_stats
            (org_code, stat_period, stat_date,
             avg_completion_rate, avg_composite_score, total_learners, total_orgs)
        SELECT
            d.org_code, 'month', '{last_month_end}',
            COALESCE(AVG(cg.completion_rate), 0),
            COALESCE(AVG(cg.total_score), 0),
            COUNT(DISTINCT u.user_id),
            COUNT(DISTINCT d.org_code)
        FROM department d
        JOIN user_info u ON u.dept_code = d.dept_code AND u.deleted_at IS NULL
        LEFT JOIN course_grade cg ON u.user_id = cg.user_id
        WHERE u.role_level = 3
        GROUP BY d.org_code
        ON DUPLICATE KEY UPDATE
            avg_completion_rate = VALUES(avg_completion_rate),
            avg_composite_score = VALUES(avg_composite_score),
            total_learners = VALUES(total_learners),
            refreshed_at = CURRENT_TIMESTAMP
    """
    await _execute_refresh("org_benchmark_stats", sql_org)


async def refresh_learner_comprehensive() -> None:
    """每小时整点：增量刷新学员综合成绩宽表。"""
    sql = """
        INSERT INTO v_learner_comprehensive
            (user_id, user_code, user_name, dept_code, dept_name, org_code,
             total_courses, courses_completed, completion_rate,
             total_study_minutes, total_study_sessions, last_studied_at)
        SELECT
            u.user_id, u.user_code, u.user_name,
            u.dept_code, d.dept_name, d.org_code,
            COUNT(DISTINCT cc.course_code) AS total_courses,
            COUNT(DISTINCT CASE WHEN lp.status = 2 THEN lp.course_code END) AS courses_completed,
            COALESCE(AVG(cg.completion_rate), 0) AS completion_rate,
            COALESCE(SUM((slog.stopped_at IS NOT NULL) * TIMESTAMPDIFF(MINUTE, slog.started_at, slog.stopped_at)), 0),
            COUNT(DISTINCT slog.id),
            MAX(slog.started_at)
        FROM user_info u
        LEFT JOIN department d ON u.dept_code = d.dept_code
        LEFT JOIN class_course cc ON EXISTS (
            SELECT 1 FROM student_class sc WHERE sc.user_id = u.user_id AND sc.class_code = cc.class_code
        )
        LEFT JOIN learning_progress lp ON u.user_id = lp.user_id AND cc.course_code = lp.course_code
        LEFT JOIN course_grade cg ON u.user_id = cg.user_id AND cc.course_code = cg.course_code
        LEFT JOIN study_session_log slog ON u.user_id = slog.user_id
        WHERE u.deleted_at IS NULL AND u.role_level = 3
        GROUP BY u.user_id, u.user_code, u.user_name, u.dept_code, d.dept_name, d.org_code
        ON DUPLICATE KEY UPDATE
            total_courses = VALUES(total_courses),
            courses_completed = VALUES(courses_completed),
            completion_rate = VALUES(completion_rate),
            total_study_minutes = VALUES(total_study_minutes),
            total_study_sessions = VALUES(total_study_sessions),
            last_studied_at = VALUES(last_studied_at),
            refreshed_at = CURRENT_TIMESTAMP
    """
    await _execute_refresh("v_learner_comprehensive", sql)


async def refresh_exam_analysis() -> None:
    """每小时 15 分：增量刷新考试分析宽表。"""
    sql = """
        INSERT INTO v_exam_analysis
            (exam_session_code, session_name, linked_course_code,
             user_code, user_id, dept_code,
             attempt_number, total_score, is_passed, is_graded, submitted_at)
        SELECT
            es.exam_session_code, es.session_name, es.linked_course_code,
            ee.user_code, ui.user_id, ui.dept_code,
            ee.attempt_number, ee.total_score,
            CASE WHEN ee.total_score >= 60 THEN 1 ELSE 0 END,
            ee.is_graded, ee.submitted_at
        FROM exam_enrollment ee
        JOIN exam_session es ON ee.exam_session_code = es.exam_session_code
        LEFT JOIN user_info ui ON ee.user_code = ui.user_code
        WHERE ee.submitted_at IS NOT NULL
        ON DUPLICATE KEY UPDATE
            total_score = VALUES(total_score),
            is_passed = VALUES(is_passed),
            is_graded = VALUES(is_graded),
            submitted_at = VALUES(submitted_at),
            refreshed_at = CURRENT_TIMESTAMP
    """
    await _execute_refresh("v_exam_analysis", sql)


async def refresh_skill_error_summary() -> None:
    """每天 03:00：追加昨日技能点错误汇总。"""
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    sql = f"""
        INSERT IGNORE INTO v_skill_error_summary
            (courseware_code, course_code, dept_code, step_index,
             total_attempts, total_errors, error_rate, unique_users,
             stat_date)
        SELECT
            courseware_code, course_code, dept_code, step_index,
            COUNT(*) AS total_attempts,
            SUM(error_count) AS total_errors,
            COALESCE(SUM(error_count) / NULLIF(COUNT(*), 0) * 100, 0) AS error_rate,
            COUNT(DISTINCT user_id) AS unique_users,
            '{yesterday}'
        FROM skill_error_log
        WHERE DATE(occurred_at) = '{yesterday}'
        GROUP BY courseware_code, course_code, dept_code, step_index
    """
    await _execute_refresh("v_skill_error_summary", sql)


async def check_and_refresh_benchmark() -> None:
    """每天 03:00 兜底检查：如果今天是 1 日且 04:00 的任务已执行则跳过，
    如果没有执行（例如服务在 04:00 未运行），则补执行。

    Phase 1 简化实现：仅在每月 1 日执行 refresh_benchmark_stats。
    """
    today = date.today()
    if today.day == 1:
        logger.info("今天是本月 1 日，执行基准统计兜底刷新")
        await refresh_benchmark_stats()
    else:
        logger.debug("今天不是 1 日，跳过基准统计检查")
