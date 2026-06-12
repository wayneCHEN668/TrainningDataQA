from datetime import datetime, date
from sqlalchemy import String, Integer, DateTime, Date, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import DECIMAL
from app.models.base import Base, TimestampMixin


class DeptBenchmarkStats(Base, TimestampMixin):
    __tablename__ = "dept_benchmark_stats"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dept_code: Mapped[str] = mapped_column(String(30), nullable=False)
    org_code: Mapped[str] = mapped_column(String(30))
    stat_period: Mapped[str] = mapped_column(String(10), default="month")
    stat_date: Mapped[date] = mapped_column(Date)
    avg_completion_rate: Mapped[float] = mapped_column(DECIMAL(5, 2), default=0.00)
    avg_exam_pass_rate: Mapped[float] = mapped_column(DECIMAL(5, 2), default=0.00)
    avg_composite_score: Mapped[float] = mapped_column(DECIMAL(6, 2), default=0.00)
    avg_study_minutes: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0.00)
    avg_skill_error_rate: Mapped[float] = mapped_column(DECIMAL(5, 2), default=0.00)
    avg_engagement_score: Mapped[float] = mapped_column(DECIMAL(5, 2), default=0.00)
    p25_completion_rate: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    p50_completion_rate: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    p75_completion_rate: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    p25_composite_score: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    p50_composite_score: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    p75_composite_score: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    total_learners: Mapped[int] = mapped_column(Integer, default=0)


class OrgBenchmarkStats(Base, TimestampMixin):
    __tablename__ = "org_benchmark_stats"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_code: Mapped[str] = mapped_column(String(30), nullable=False)
    stat_period: Mapped[str] = mapped_column(String(10), default="month")
    stat_date: Mapped[date] = mapped_column(Date)
    avg_completion_rate: Mapped[float] = mapped_column(DECIMAL(5, 2), default=0.00)
    avg_exam_pass_rate: Mapped[float] = mapped_column(DECIMAL(5, 2), default=0.00)
    avg_composite_score: Mapped[float] = mapped_column(DECIMAL(6, 2), default=0.00)
    avg_study_minutes: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0.00)
    avg_skill_error_rate: Mapped[float] = mapped_column(DECIMAL(5, 2), default=0.00)
    avg_engagement_score: Mapped[float] = mapped_column(DECIMAL(5, 2), default=0.00)
    p25_completion_rate: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    p50_completion_rate: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    p75_completion_rate: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    p25_composite_score: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    p50_composite_score: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    p75_composite_score: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    total_orgs: Mapped[int] = mapped_column(Integer, default=0)
    total_learners: Mapped[int] = mapped_column(Integer, default=0)


class LearnerComprehensive(Base, TimestampMixin):
    __tablename__ = "v_learner_comprehensive"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    user_code: Mapped[str | None] = mapped_column(String(30))
    user_name: Mapped[str | None] = mapped_column(String(100))
    dept_code: Mapped[str | None] = mapped_column(String(30))
    dept_name: Mapped[str | None] = mapped_column(String(100))
    org_code: Mapped[str | None] = mapped_column(String(30))
    class_code: Mapped[str | None] = mapped_column(String(30))
    class_name: Mapped[str | None] = mapped_column(String(100))
    total_courses: Mapped[int] = mapped_column(Integer, default=0)
    courses_completed: Mapped[int] = mapped_column(Integer, default=0)
    completion_rate: Mapped[float] = mapped_column(DECIMAL(5, 2), default=0.00)
    avg_composite_score: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    avg_courseware_score: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    avg_exam_score: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    avg_assignment_score: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    grade_rank: Mapped[str | None] = mapped_column(String(10))
    total_exams_taken: Mapped[int] = mapped_column(Integer, default=0)
    exams_passed: Mapped[int] = mapped_column(Integer, default=0)
    exam_pass_rate: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    best_exam_score: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    total_study_minutes: Mapped[int] = mapped_column(Integer, default=0)
    total_study_sessions: Mapped[int] = mapped_column(Integer, default=0)
    avg_session_minutes: Mapped[int | None] = mapped_column(Integer)
    last_studied_at: Mapped[datetime | None] = mapped_column(DateTime)
    is_at_risk: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_type: Mapped[str | None] = mapped_column(String(50))
    days_since_last_study: Mapped[int | None] = mapped_column(Integer)


class ExamAnalysis(Base, TimestampMixin):
    __tablename__ = "v_exam_analysis"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    exam_session_code: Mapped[str] = mapped_column(String(30), nullable=False)
    session_name: Mapped[str | None] = mapped_column(String(200))
    open_at: Mapped[datetime | None] = mapped_column(DateTime)
    close_at: Mapped[datetime | None] = mapped_column(DateTime)
    org_code: Mapped[str | None] = mapped_column(String(30))
    linked_course_code: Mapped[str | None] = mapped_column(String(30))
    user_code: Mapped[str] = mapped_column(String(30))
    user_id: Mapped[str | None] = mapped_column(String(50))
    dept_code: Mapped[str | None] = mapped_column(String(30))
    attempt_number: Mapped[int] = mapped_column(Integer, default=0)
    total_score: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    is_passed: Mapped[bool | None] = mapped_column(Boolean)
    is_graded: Mapped[bool] = mapped_column(Boolean, default=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    type_scores: Mapped[dict | None] = mapped_column(JSON)
    correct_count: Mapped[int | None] = mapped_column(Integer)
    total_questions: Mapped[int | None] = mapped_column(Integer)
    accuracy_rate: Mapped[float | None] = mapped_column(DECIMAL(5, 2))


class SkillErrorSummary(Base, TimestampMixin):
    __tablename__ = "v_skill_error_summary"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    courseware_code: Mapped[str] = mapped_column(String(30), nullable=False)
    courseware_name: Mapped[str | None] = mapped_column(String(100))
    course_code: Mapped[str | None] = mapped_column(String(30))
    dept_code: Mapped[str | None] = mapped_column(String(30))
    step_index: Mapped[int] = mapped_column(Integer)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0)
    total_errors: Mapped[int] = mapped_column(Integer, default=0)
    error_rate: Mapped[float] = mapped_column(DECIMAL(5, 2), default=0.00)
    unique_users: Mapped[int] = mapped_column(Integer, default=0)
    avg_errors_per_user: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    stat_date: Mapped[date] = mapped_column(Date)
