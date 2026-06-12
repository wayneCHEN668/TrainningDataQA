"""ToolRegistry: 13 LangChain StructuredTools for the SkillCloudHS agent.

Largest file in Phase 4 (~500 lines).

Architecture:
  - Holds a QueryExecutor instance for all query-type tools (Q1-Q8, A1-A2).
  - 13 _make_* methods, each returning a StructuredTool.from_function().
  - get_all_tools() returns the full list for injection into the ReAct agent.

Query tools (Q1-Q8) query wide tables/views via SQLAlchemy Core.
Compute tools (C1-C3) are pure Python, no DB.
Auxiliary tools (A1-A2) query benchmark/stats and course/exam lookup tables.
"""

from collections import defaultdict
import statistics

from langchain_core.tools import StructuredTool
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserContext
from app.services.ai.schema_index import SchemaIndexService
from app.services.query.query_executor import QueryExecutor


# ---------------------------------------------------------------------------
# ToolRegistry
# ---------------------------------------------------------------------------

class ToolRegistry:
    """Registry of all 13 StructuredTools for the SkillCloudHS agent."""

    def __init__(
        self,
        db: AsyncSession,
        user_ctx: UserContext,
        schema_svc: SchemaIndexService,
    ):
        self._executor = QueryExecutor(db, user_ctx, schema_svc)

    # -- public --------------------------------------------------------------

    def get_all_tools(self) -> list[StructuredTool]:
        return [
            self._make_query_completion_rate(),
            self._make_query_incomplete_learners(),
            self._make_query_exam_performance(),
            self._make_query_skill_error_analysis(),
            self._make_query_learning_trend(),
            self._make_query_at_risk_learners(),
            self._make_query_individual_profile(),
            self._make_query_org_overview(),
            self._make_compute_period_comparison(),
            self._make_detect_anomalies(),
            self._make_evaluate_metric_level(),
            self._make_get_benchmark(),
            self._make_search_course_or_exam(),
        ]

    # === Query Tools (Q1-Q8) ================================================

    # -- Q1: query_completion_rate -------------------------------------------

    def _make_query_completion_rate(self) -> StructuredTool:
        from app.models.benchmark import LearnerComprehensive
        from app.schemas.tools import CompletionRateInput

        async def _run(scope_type, time_start, time_end, course_code=None, group_by="none"):
            lc = LearnerComprehensive.__table__
            cols = [
                lc.c.user_id, lc.c.user_name, lc.c.dept_name,
                lc.c.completion_rate, lc.c.total_courses, lc.c.courses_completed,
                lc.c.org_code, lc.c.dept_code, lc.c.class_name, lc.c.class_code,
            ]
            stmt = select(*cols)
            if course_code:
                stmt = stmt.where(lc.c.completion_rate >= 0)  # ensure data exists
            rows = await self._executor.execute(stmt)

            if not rows:
                return {"completion_rate": 0, "total_learners": 0, "breakdown": []}

            avg_rate = sum(r["completion_rate"] for r in rows) / len(rows)
            breakdown = []
            if group_by == "dept":
                groups: dict = defaultdict(list)
                for r in rows:
                    groups[r.get("dept_name", "Unknown")].append(r["completion_rate"])
                breakdown = [
                    {"group": k, "rate": round(sum(v) / len(v), 2), "count": len(v)}
                    for k, v in groups.items()
                ]
            elif group_by == "class":
                groups: dict = defaultdict(list)
                for r in rows:
                    groups[r.get("class_name", "Unknown")].append(r["completion_rate"])
                breakdown = [
                    {"group": k, "rate": round(sum(v) / len(v), 2), "count": len(v)}
                    for k, v in groups.items()
                ]
            elif group_by == "course":
                groups: dict = defaultdict(list)
                for r in rows:
                    groups[r.get("class_name", "Unknown")].append(r["completion_rate"])
                breakdown = [
                    {"group": k, "rate": round(sum(v) / len(v), 2), "count": len(v)}
                    for k, v in groups.items()
                ]

            return {
                "completion_rate": round(avg_rate, 2),
                "total_learners": len(rows),
                "breakdown": breakdown,
            }

        return StructuredTool.from_function(
            coroutine=_run,
            name="query_completion_rate",
            description="Query learning completion rate. Use for: completion percentage, which depts/classes have low completion. group_by can be dept/class/course.",
            args_schema=CompletionRateInput,
        )

    # -- Q2: query_incomplete_learners ---------------------------------------

    def _make_query_incomplete_learners(self) -> StructuredTool:
        from app.models.benchmark import LearnerComprehensive
        from app.schemas.tools import IncompleteLearnersInput

        async def _run(scope_type, course_code, urgency_threshold_days=7):
            lc = LearnerComprehensive.__table__
            cols = [
                lc.c.user_id, lc.c.user_name, lc.c.dept_name, lc.c.dept_code,
                lc.c.completion_rate, lc.c.total_courses, lc.c.courses_completed,
                lc.c.days_since_last_study, lc.c.is_at_risk, lc.c.risk_type,
                lc.c.last_studied_at, lc.c.org_code,
            ]
            stmt = select(*cols).where(lc.c.completion_rate < 100)
            rows = await self._executor.execute(stmt)

            if not rows:
                return {"incomplete_count": 0, "learners": [], "summary": ""}

            learners = []
            urgent_count = 0
            for r in rows:
                entry = {
                    "user_id": r["user_id"],
                    "user_name": r.get("user_name"),
                    "dept_name": r.get("dept_name"),
                    "completion_rate": r["completion_rate"],
                    "total_courses": r["total_courses"],
                    "courses_completed": r["courses_completed"],
                    "days_since_last_study": r.get("days_since_last_study"),
                    "is_at_risk": bool(r.get("is_at_risk")),
                    "risk_type": r.get("risk_type"),
                }
                if (r.get("days_since_last_study") or 0) >= urgency_threshold_days:
                    entry["urgent"] = True
                    urgent_count += 1
                else:
                    entry["urgent"] = False
                learners.append(entry)

            return {
                "incomplete_count": len(rows),
                "urgent_count": urgent_count,
                "learners": learners,
                "summary": f"{len(rows)} learners have not completed; {urgent_count} are urgent (inactive >= {urgency_threshold_days} days).",
            }

        return StructuredTool.from_function(
            coroutine=_run,
            name="query_incomplete_learners",
            description="Find learners who have NOT completed a course (completion_rate < 100). Use for: identifying learners needing follow-up, which courses have high unfinished rates.",
            args_schema=IncompleteLearnersInput,
        )

    # -- Q3: query_exam_performance ------------------------------------------

    def _make_query_exam_performance(self) -> StructuredTool:
        from app.models.benchmark import ExamAnalysis
        from app.schemas.tools import ExamPerformanceInput

        async def _run(scope_type, exam_session_code=None, time_start=None, time_end=None, group_by="none"):
            ea = ExamAnalysis.__table__
            cols = [
                ea.c.exam_session_code, ea.c.session_name,
                ea.c.user_code, ea.c.user_id, ea.c.dept_code,
                ea.c.total_score, ea.c.is_passed, ea.c.is_graded,
                ea.c.accuracy_rate, ea.c.duration_seconds,
                ea.c.correct_count, ea.c.total_questions,
                ea.c.open_at, ea.c.close_at,
            ]
            stmt = select(*cols).where(ea.c.is_graded == True)
            if exam_session_code:
                stmt = stmt.where(ea.c.exam_session_code == exam_session_code)
            rows = await self._executor.execute(stmt)

            if not rows:
                return {"total_exams": 0, "pass_rate": 0, "avg_score": 0, "breakdown": []}

            total = len(rows)
            passed = sum(1 for r in rows if r.get("is_passed"))
            pass_rate = round(passed / total * 100, 2) if total else 0
            avg_score = round(sum(r["total_score"] or 0 for r in rows) / total, 2)
            avg_accuracy = round(sum(r["accuracy_rate"] or 0 for r in rows) / total, 2)

            breakdown = []
            if group_by == "dept":
                groups: dict = defaultdict(list)
                for r in rows:
                    groups[r.get("dept_code", "Unknown")].append(r["total_score"] or 0)
                breakdown = [
                    {"group": k, "avg_score": round(sum(v) / len(v), 2), "count": len(v)}
                    for k, v in groups.items()
                ]
            elif group_by == "exam":
                groups: dict = defaultdict(list)
                for r in rows:
                    groups[r.get("session_name", r.get("exam_session_code", "Unknown"))].append(r["total_score"] or 0)
                breakdown = [
                    {"group": k, "avg_score": round(sum(v) / len(v), 2), "count": len(v)}
                    for k, v in groups.items()
                ]

            return {
                "total_exams": total,
                "passed_count": passed,
                "pass_rate": pass_rate,
                "avg_score": avg_score,
                "avg_accuracy": avg_accuracy,
                "breakdown": breakdown,
            }

        return StructuredTool.from_function(
            coroutine=_run,
            name="query_exam_performance",
            description="Query exam results from v_exam_analysis. Use for: exam pass rates, score distributions by dept/exam, overall exam performance trends.",
            args_schema=ExamPerformanceInput,
        )

    # -- Q4: query_skill_error_analysis --------------------------------------

    def _make_query_skill_error_analysis(self) -> StructuredTool:
        from app.models.benchmark import SkillErrorSummary
        from app.schemas.tools import SkillErrorInput

        async def _run(courseware_code, top_n=10):
            ses = SkillErrorSummary.__table__
            cols = [
                ses.c.courseware_code, ses.c.courseware_name,
                ses.c.step_index, ses.c.total_attempts, ses.c.total_errors,
                ses.c.error_rate, ses.c.unique_users, ses.c.avg_errors_per_user,
                ses.c.stat_date, ses.c.course_code, ses.c.dept_code,
            ]
            stmt = select(*cols).where(ses.c.courseware_code == courseware_code)
            stmt = stmt.order_by(ses.c.error_rate.desc()).limit(top_n)
            rows = await self._executor.execute(stmt)

            if not rows:
                return {"courseware_code": courseware_code, "top_errors": [], "total_error_steps": 0}

            top_errors = []
            for r in rows:
                top_errors.append({
                    "step_index": r["step_index"],
                    "total_attempts": r["total_attempts"],
                    "total_errors": r["total_errors"],
                    "error_rate": r["error_rate"],
                    "unique_users": r["unique_users"],
                    "avg_errors_per_user": r.get("avg_errors_per_user"),
                })

            return {
                "courseware_code": courseware_code,
                "courseware_name": rows[0].get("courseware_name") if rows else None,
                "top_errors": top_errors,
                "total_error_steps": len(rows),
            }

        return StructuredTool.from_function(
            coroutine=_run,
            name="query_skill_error_analysis",
            description="Analyze skill error hotspots for a specific courseware. Use for: finding which skill points cause most errors, where learners get stuck.",
            args_schema=SkillErrorInput,
        )

    # -- Q5: query_learning_trend --------------------------------------------

    def _make_query_learning_trend(self) -> StructuredTool:
        from app.models.stats import OrgDailyStats
        from app.schemas.tools import LearningTrendInput

        async def _run(scope_type, metric, time_start, time_end, granularity="week"):
            ods = OrgDailyStats.__table__
            metric_map = {
                "study_minutes": ods.c.total_study_minutes,
                "completions": ods.c.courseware_completed,
                "exam_pass": ods.c.exam_completed,
                "active_users": ods.c.active_users,
            }
            metric_col = metric_map.get(metric, ods.c.total_study_minutes)
            cols = [ods.c.stat_date, metric_col, ods.c.active_users, ods.c.org_code]
            stmt = select(*cols).order_by(ods.c.stat_date.asc())
            rows = await self._executor.execute(stmt)

            if not rows:
                return {"metric": metric, "data_points": [], "trend": "no_data"}

            data_points = []
            for r in rows:
                data_points.append({
                    "date": str(r["stat_date"]),
                    "value": float(r[metric_col.key] if hasattr(r, metric_col.key) else r.get(metric_col.key, 0) or 0),
                })

            # Compute trend direction
            values = [d["value"] for d in data_points if d["value"]]
            if len(values) >= 2:
                if values[-1] > values[0] * 1.05:
                    trend = "up"
                elif values[-1] < values[0] * 0.95:
                    trend = "down"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"

            return {
                "metric": metric,
                "data_points": data_points,
                "trend": trend,
                "granularity": granularity,
            }

        return StructuredTool.from_function(
            coroutine=_run,
            name="query_learning_trend",
            description="Query daily learning activity trends. Use for: study minutes over time, completion trends, active user trends. metric can be study_minutes/completions/exam_pass/active_users.",
            args_schema=LearningTrendInput,
        )

    # -- Q6: query_at_risk_learners ------------------------------------------

    def _make_query_at_risk_learners(self) -> StructuredTool:
        from app.models.benchmark import LearnerComprehensive
        from app.schemas.tools import AtRiskLearnersInput

        async def _run(scope_type, risk_types=None):
            if risk_types is None:
                risk_types = ["inactive", "low_score", "near_deadline"]
            lc = LearnerComprehensive.__table__
            cols = [
                lc.c.user_id, lc.c.user_name, lc.c.user_code,
                lc.c.dept_name, lc.c.dept_code, lc.c.org_code,
                lc.c.completion_rate, lc.c.avg_composite_score,
                lc.c.days_since_last_study, lc.c.risk_type,
                lc.c.is_at_risk, lc.c.last_studied_at,
                lc.c.total_courses, lc.c.courses_completed,
            ]
            stmt = select(*cols).where(lc.c.is_at_risk == True)
            rows = await self._executor.execute(stmt)

            if not rows:
                return {"at_risk_count": 0, "learners": [], "summary": "No at-risk learners found."}

            learners = []
            risk_summary: dict = defaultdict(int)
            for r in rows:
                risk = r.get("risk_type", "unknown")
                risk_summary[risk] += 1
                learners.append({
                    "user_id": r["user_id"],
                    "user_name": r.get("user_name"),
                    "user_code": r.get("user_code"),
                    "dept_name": r.get("dept_name"),
                    "completion_rate": r["completion_rate"],
                    "avg_composite_score": r.get("avg_composite_score"),
                    "days_since_last_study": r.get("days_since_last_study"),
                    "risk_type": risk,
                })

            return {
                "at_risk_count": len(rows),
                "risk_breakdown": dict(risk_summary),
                "learners": learners,
                "summary": f"{len(rows)} at-risk learners: {dict(risk_summary)}",
            }

        return StructuredTool.from_function(
            coroutine=_run,
            name="query_at_risk_learners",
            description="Query learners flagged as at-risk (is_at_risk=1). Use for: identifying learners needing intervention, risk distribution by type.",
            args_schema=AtRiskLearnersInput,
        )

    # -- Q7: query_individual_profile ----------------------------------------

    def _make_query_individual_profile(self) -> StructuredTool:
        from app.models.path import LearnerProfile
        from app.models.progress import CourseGrade
        from app.schemas.tools import IndividualProfileInput

        async def _run(user_code):
            # 1. Learner profile
            lp = LearnerProfile.__table__
            profile_result = await self._executor.execute(
                select(lp).where(lp.c.user_id == user_code).limit(1)
            )
            profile = profile_result[0] if profile_result else None

            # 2. Course grades (use user_id matching, fall back to the id)
            cg = CourseGrade.__table__
            grade_rows = await self._executor.execute(
                select(cg).where(cg.c.user_id == user_code)
            )

            courses = []
            for gr in grade_rows:
                courses.append({
                    "course_code": gr.get("course_code"),
                    "completion_rate": gr.get("completion_rate"),
                    "total_score": gr.get("total_score"),
                    "grade_rank": gr.get("grade_rank"),
                    "is_passed": bool(gr.get("is_passed", False)),
                    "courseware_score": gr.get("courseware_score"),
                    "exam_score": gr.get("exam_score"),
                })

            if not profile:
                return {"found": False, "user_code": user_code, "message": "Learner profile not found."}

            return {
                "found": True,
                "user_code": user_code,
                "profile": {
                    "avg_session_minutes": profile.get("avg_session_minutes"),
                    "avg_completion_rate": profile.get("avg_completion_rate"),
                    "total_study_minutes": profile.get("total_study_minutes"),
                    "total_courses_completed": profile.get("total_courses_completed"),
                    "strong_domains": profile.get("strong_domains"),
                    "weak_domains": profile.get("weak_domains"),
                    "learning_style": profile.get("learning_style"),
                    "study_pace": profile.get("study_pace"),
                    "engagement_score": profile.get("engagement_score"),
                    "profile_summary": profile.get("profile_summary"),
                },
                "courses": courses,
            }

        return StructuredTool.from_function(
            coroutine=_run,
            name="query_individual_profile",
            description="Query a single learner's full profile including learning style, course grades, and study habits. Use for: checking an individual's progress, weak domains, and performance.",
            args_schema=IndividualProfileInput,
        )

    # -- Q8: query_org_overview ----------------------------------------------

    def _make_query_org_overview(self) -> StructuredTool:
        from app.models.stats import OrgDailyStats
        from app.models.progress import CourseGrade
        from app.schemas.tools import OrgOverviewInput

        async def _run(time_start, time_end):
            # 1. Org daily stats aggregation
            ods = OrgDailyStats.__table__
            agg_rows = await self._executor.execute(
                select(
                    ods.c.org_code,
                    func.sum(ods.c.total_study_minutes).label("total_study_minutes"),
                    func.sum(ods.c.courseware_completed).label("total_completions"),
                    func.sum(ods.c.exam_completed).label("total_exams"),
                    func.max(ods.c.active_users).label("peak_active_users"),
                    func.sum(ods.c.study_sessions).label("total_sessions"),
                ).group_by(ods.c.org_code)
            )

            org_stats = []
            for row in agg_rows:
                org_stats.append({
                    "org_code": row["org_code"],
                    "total_study_minutes": float(row["total_study_minutes"] or 0),
                    "total_completions": int(row["total_completions"] or 0),
                    "total_exams": int(row["total_exams"] or 0),
                    "peak_active_users": int(row["peak_active_users"] or 0),
                    "total_sessions": int(row["total_sessions"] or 0),
                })

            # 2. Course grade summary
            cg = CourseGrade.__table__
            grade_rows = await self._executor.execute(
                select(
                    func.count().label("total_records"),
                    func.avg(cg.c.completion_rate).label("avg_completion_rate"),
                    func.avg(cg.c.total_score).label("avg_total_score"),
                    func.count().filter(cg.c.is_passed == True).label("passed_count"),
                )
            )
            grade_summary = grade_rows[0] if grade_rows else None

            return {
                "org_stats": org_stats,
                "grade_summary": {
                    "avg_completion_rate": round(float(grade_summary["avg_completion_rate"] or 0), 2),
                    "avg_total_score": round(float(grade_summary["avg_total_score"] or 0), 2),
                    "passed_count": int(grade_summary["passed_count"] or 0),
                    "total_records": int(grade_summary["total_records"] or 0),
                } if grade_summary else {},
            }

        return StructuredTool.from_function(
            coroutine=_run,
            name="query_org_overview",
            description="Get high-level org overview: aggregated study stats by org + overall grade summary. Use for: org-level dashboards, cross-org comparisons.",
            args_schema=OrgOverviewInput,
        )

    # === Compute Tools (C1-C3) ==============================================

    # -- C1: compute_period_comparison ---------------------------------------

    def _make_compute_period_comparison(self) -> StructuredTool:
        from app.schemas.tools import PeriodComparisonInput

        async def _run(data_current, data_previous, key_field):
            if not data_current or not data_previous:
                return {"error": "Both data_current and data_previous must be non-empty lists."}
            curr_avg = sum(d[key_field] for d in data_current) / len(data_current)
            prev_avg = sum(d[key_field] for d in data_previous) / len(data_previous)
            delta = round(curr_avg - prev_avg, 2)
            delta_pct = round((delta / prev_avg * 100), 2) if prev_avg else 0
            return {
                "current_avg": round(curr_avg, 2),
                "previous_avg": round(prev_avg, 2),
                "delta": delta,
                "delta_pct": delta_pct,
            }

        return StructuredTool.from_function(
            coroutine=_run,
            name="compute_period_comparison",
            description="Compare two periods (current vs previous). Returns delta and percentage change. Use for: MoM/QoQ comparisons of any metric.",
            args_schema=PeriodComparisonInput,
        )

    # -- C2: detect_anomalies ------------------------------------------------

    def _make_detect_anomalies(self) -> StructuredTool:
        from app.schemas.tools import AnomalyDetectionInput

        async def _run(data_points, threshold_sigma=2.0):
            if not data_points or len(data_points) < 2:
                return {"anomalies": [], "mean": 0, "stdev": 0, "message": "Need at least 2 data points."}

            values = [d["value"] for d in data_points]
            mean = statistics.mean(values)
            stdev = statistics.stdev(values)
            anomalies = []
            for d in data_points:
                deviation = abs(d["value"] - mean) / stdev if stdev > 0 else 0
                if deviation > threshold_sigma:
                    anomalies.append({
                        "period": d.get("date", ""),
                        "value": d["value"],
                        "deviation_sigma": round(deviation, 2),
                    })
            return {
                "anomalies": anomalies,
                "mean": round(mean, 2),
                "stdev": round(stdev, 2),
            }

        return StructuredTool.from_function(
            coroutine=_run,
            name="detect_anomalies",
            description="Detect statistical anomalies in time series data using sigma threshold. Use for: finding unusual spikes/drops in metrics.",
            args_schema=AnomalyDetectionInput,
        )

    # -- C3: evaluate_metric_level -------------------------------------------

    def _make_evaluate_metric_level(self) -> StructuredTool:
        from app.schemas.tools import MetricLevelInput

        async def _run(metric_value, benchmark_value, percentile_bands=None):
            ratio = metric_value / benchmark_value if benchmark_value else 0
            if percentile_bands:
                p75 = percentile_bands.get("p75", 0)
                p50 = percentile_bands.get("p50", 0)
                p25 = percentile_bands.get("p25", 0)
                if metric_value >= p75:
                    level = "excellent"
                elif metric_value >= p50:
                    level = "good"
                elif metric_value >= p25:
                    level = "average"
                else:
                    level = "below"
            else:
                if ratio >= 1.2:
                    level = "excellent"
                elif ratio >= 1.0:
                    level = "good"
                elif ratio >= 0.8:
                    level = "average"
                elif ratio >= 0.6:
                    level = "below"
                else:
                    level = "poor"
            return {
                "level": level,
                "ratio": round(ratio, 2),
                "gap_to_average": round(metric_value - benchmark_value, 2),
            }

        return StructuredTool.from_function(
            coroutine=_run,
            name="evaluate_metric_level",
            description="Evaluate a metric value against benchmarks: excellent/good/average/below/poor. Use for: interpreting raw numbers in context.",
            args_schema=MetricLevelInput,
        )

    # === Auxiliary Tools (A1-A2) ============================================

    # -- A1: get_benchmark ---------------------------------------------------

    def _make_get_benchmark(self) -> StructuredTool:
        from app.models.benchmark import DeptBenchmarkStats, OrgBenchmarkStats
        from app.schemas.tools import BenchmarkInput

        async def _run(scope_type, scope_code, stat_period="month"):
            if scope_type == "dept":
                dbs = DeptBenchmarkStats.__table__
                cols = [
                    dbs.c.dept_code, dbs.c.stat_period, dbs.c.stat_date,
                    dbs.c.avg_completion_rate, dbs.c.avg_exam_pass_rate,
                    dbs.c.avg_composite_score, dbs.c.avg_study_minutes,
                    dbs.c.avg_skill_error_rate, dbs.c.avg_engagement_score,
                    dbs.c.p25_completion_rate, dbs.c.p50_completion_rate,
                    dbs.c.p75_completion_rate, dbs.c.total_learners,
                ]
                stmt = select(*cols).where(
                    dbs.c.dept_code == scope_code,
                    dbs.c.stat_period == stat_period,
                ).order_by(dbs.c.stat_date.desc()).limit(1)
            else:
                obs = OrgBenchmarkStats.__table__
                cols = [
                    obs.c.org_code, obs.c.stat_period, obs.c.stat_date,
                    obs.c.avg_completion_rate, obs.c.avg_exam_pass_rate,
                    obs.c.avg_composite_score, obs.c.avg_study_minutes,
                    obs.c.avg_skill_error_rate, obs.c.avg_engagement_score,
                    obs.c.p25_completion_rate, obs.c.p50_completion_rate,
                    obs.c.p75_completion_rate, obs.c.total_learners, obs.c.total_orgs,
                ]
                stmt = select(*cols).where(
                    obs.c.org_code == scope_code,
                    obs.c.stat_period == stat_period,
                ).order_by(obs.c.stat_date.desc()).limit(1)

            rows = await self._executor.execute(stmt)
            if not rows:
                return {"found": False, "scope_type": scope_type, "scope_code": scope_code}

            r = rows[0]
            return {
                "found": True,
                "scope_type": scope_type,
                "scope_code": scope_code,
                "stat_period": r.get("stat_period"),
                "stat_date": str(r.get("stat_date")) if r.get("stat_date") else None,
                "benchmark": {
                    "avg_completion_rate": r.get("avg_completion_rate"),
                    "avg_exam_pass_rate": r.get("avg_exam_pass_rate"),
                    "avg_composite_score": r.get("avg_composite_score"),
                    "avg_study_minutes": r.get("avg_study_minutes"),
                    "avg_skill_error_rate": r.get("avg_skill_error_rate"),
                    "avg_engagement_score": r.get("avg_engagement_score"),
                    "p25_completion_rate": r.get("p25_completion_rate"),
                    "p50_completion_rate": r.get("p50_completion_rate"),
                    "p75_completion_rate": r.get("p75_completion_rate"),
                    "total_learners": r.get("total_learners"),
                },
            }

        return StructuredTool.from_function(
            coroutine=_run,
            name="get_benchmark",
            description="Get dept or org benchmark stats (averages + percentiles). Use for: comparing a metric against peers, finding what good looks like.",
            args_schema=BenchmarkInput,
        )

    # -- A2: search_course_or_exam -------------------------------------------

    def _make_search_course_or_exam(self) -> StructuredTool:
        from app.models.course import Course
        from app.models.exam import ExamSession
        from app.schemas.tools import SearchCourseExamInput

        async def _run(query, search_type="all"):
            results = []

            if search_type in ("course", "all"):
                c = Course.__table__
                course_rows = await self._executor.execute(
                    select(c.c.course_code, c.c.course_name, c.c.course_desc, c.c.dept_code)
                    .where(
                        c.c.course_name.contains(query)
                        | c.c.course_code.contains(query)
                    )
                    .limit(10)
                )
                for r in course_rows:
                    results.append({
                        "type": "course",
                        "code": r["course_code"],
                        "name": r["course_name"],
                        "desc": r.get("course_desc"),
                        "dept_code": r.get("dept_code"),
                    })

            if search_type in ("exam", "all"):
                es = ExamSession.__table__
                exam_rows = await self._executor.execute(
                    select(es.c.exam_session_code, es.c.session_name, es.c.status, es.c.org_code)
                    .where(
                        es.c.session_name.contains(query)
                        | es.c.exam_session_code.contains(query)
                    )
                    .limit(10)
                )
                for r in exam_rows:
                    results.append({
                        "type": "exam_session",
                        "code": r["exam_session_code"],
                        "name": r["session_name"],
                        "status": r.get("status"),
                        "org_code": r.get("org_code"),
                    })

            return {
                "query": query,
                "search_type": search_type,
                "count": len(results),
                "results": results,
            }

        return StructuredTool.from_function(
            coroutine=_run,
            name="search_course_or_exam",
            description="Fuzzy search courses and exam sessions by name or code. Use for: finding course/exam codes before querying other tools.",
            args_schema=SearchCourseExamInput,
        )
