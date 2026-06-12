"""APScheduler 配置与任务注册。"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.jobs.refresh_wide_tables import (
    refresh_benchmark_stats,
    refresh_learner_comprehensive,
    refresh_exam_analysis,
    refresh_skill_error_summary,
    check_and_refresh_benchmark,
)

scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


def register_jobs() -> None:
    # 基准统计：每月 1 日 04:00
    scheduler.add_job(
        refresh_benchmark_stats,
        trigger="cron",
        hour=4, minute=0, day=1,
        id="refresh_benchmark_stats",
        name="刷新院系/机构基准统计",
        replace_existing=True,
    )

    # 学员综合宽表：每小时整点
    scheduler.add_job(
        refresh_learner_comprehensive,
        trigger="cron",
        minute=0,
        id="refresh_learner_comprehensive",
        name="刷新学员综合成绩宽表",
        replace_existing=True,
    )

    # 考试分析宽表：每小时 15 分
    scheduler.add_job(
        refresh_exam_analysis,
        trigger="cron",
        minute=15,
        id="refresh_exam_analysis",
        name="刷新考试分析宽表",
        replace_existing=True,
    )

    # 技能点错误汇总：每天 03:00
    scheduler.add_job(
        refresh_skill_error_summary,
        trigger="cron",
        hour=3, minute=0,
        id="refresh_skill_error_summary",
        name="刷新技能点错误汇总",
        replace_existing=True,
    )

    # 基准统计兜底检查：每天 03:00
    scheduler.add_job(
        check_and_refresh_benchmark,
        trigger="cron",
        hour=3, minute=0,
        id="check_benchmark",
        name="检查基准统计是否需要刷新",
        replace_existing=True,
    )
