from datetime import datetime, date
from sqlalchemy import String, Integer, Date, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import DECIMAL
from app.models.base import Base


class OrgDailyStats(Base):
    __tablename__ = "org_daily_stats"
    __table_args__ = {"keep_existing": True}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_code: Mapped[str] = mapped_column(String(30))
    stat_date: Mapped[date] = mapped_column(Date)
    study_sessions: Mapped[int] = mapped_column(Integer, default=0)
    total_study_minutes: Mapped[float] = mapped_column(DECIMAL(12, 2))
    courseware_completed: Mapped[int] = mapped_column(Integer, default=0)
    skill_points_completed: Mapped[int] = mapped_column(Integer, default=0)
    exam_completed: Mapped[int] = mapped_column(Integer, default=0)
    experiment_minutes: Mapped[float] = mapped_column(DECIMAL(12, 2))
    qa_asked: Mapped[int] = mapped_column(Integer, default=0)
    qa_answered: Mapped[int] = mapped_column(Integer, default=0)
    active_users: Mapped[int] = mapped_column(Integer, default=0)
    login_times: Mapped[int] = mapped_column(Integer, default=0)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class OrgMonthlyStats(Base):
    __tablename__ = "org_monthly_stats"
    __table_args__ = {"keep_existing": True}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    app_id: Mapped[str] = mapped_column(String(30))
    stat_month: Mapped[date] = mapped_column(Date)
    total_study_minutes: Mapped[int] = mapped_column(Integer, default=0)
    total_study_sessions: Mapped[int] = mapped_column(Integer, default=0)
    active_users: Mapped[int] = mapped_column(Integer, default=0)
    avg_study_minutes: Mapped[float] = mapped_column(DECIMAL(10, 2))
    avg_study_sessions: Mapped[float] = mapped_column(DECIMAL(10, 2))
    avg_courseware_done: Mapped[float] = mapped_column(DECIMAL(10, 2))
    avg_skill_points_done: Mapped[float] = mapped_column(DECIMAL(10, 2))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class OrgCourseStats(Base):
    __tablename__ = "org_course_stats"
    __table_args__ = {"keep_existing": True}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_code: Mapped[str] = mapped_column(String(30))
    course_code: Mapped[str] = mapped_column(String(30))
    stat_date: Mapped[date] = mapped_column(Date)
    total_study_minutes: Mapped[float] = mapped_column(DECIMAL(12, 2))
    completions: Mapped[int] = mapped_column(Integer, default=0)
    active_learners: Mapped[int] = mapped_column(Integer, default=0)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class CoursewareStudyStats(Base):
    __tablename__ = "courseware_study_stats"
    __table_args__ = {"keep_existing": True}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    app_id: Mapped[str | None] = mapped_column(String(30))
    courseware_key: Mapped[str | None] = mapped_column(String(30))
    courseware_name: Mapped[str | None] = mapped_column(String(100))
    total_minutes: Mapped[float] = mapped_column(DECIMAL(12, 2))
    study_minutes: Mapped[float] = mapped_column(DECIMAL(12, 2))
    qa_minutes: Mapped[float] = mapped_column(DECIMAL(12, 2))
    stat_date: Mapped[date | None] = mapped_column(Date)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
