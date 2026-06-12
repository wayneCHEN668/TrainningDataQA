from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import DECIMAL
from app.models.base import Base


class LearningProgress(Base):
    __tablename__ = "learning_progress"
    __table_args__ = {"keep_existing": True}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50))
    course_code: Mapped[str] = mapped_column(String(30))
    courseware_code: Mapped[str] = mapped_column(String(30))
    type_code: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[int] = mapped_column(Integer, default=0)
    best_score: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    last_score: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    total_study_minutes: Mapped[int] = mapped_column(Integer, default=0)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    first_started_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_studied_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class CourseGrade(Base):
    __tablename__ = "course_grade"
    __table_args__ = {"keep_existing": True}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50))
    course_code: Mapped[str] = mapped_column(String(30))
    class_code: Mapped[str | None] = mapped_column(String(30))
    position_code: Mapped[str | None] = mapped_column(String(30))
    courseware_score: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    exam_score: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    assignment_score: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    total_score: Mapped[float | None] = mapped_column(DECIMAL(6, 2))
    grade_rank: Mapped[str | None] = mapped_column(String(10))
    total_courseware: Mapped[int] = mapped_column(Integer, default=0)
    completed_courseware: Mapped[int] = mapped_column(Integer, default=0)
    completion_rate: Mapped[float] = mapped_column(DECIMAL(5, 2))
    exam_attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    assignment_submit_count: Mapped[int] = mapped_column(Integer, default=0)
    last_studied_at: Mapped[datetime | None] = mapped_column(DateTime)
    is_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    passed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
