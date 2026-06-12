from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class StudySessionLog(Base):
    __tablename__ = "study_session_log"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50))
    user_code: Mapped[str | None] = mapped_column(String(30))
    courseware_key: Mapped[str] = mapped_column(String(30))
    courseware_name: Mapped[str | None] = mapped_column(String(100))
    course_code: Mapped[str | None] = mapped_column(String(30))
    dept_code: Mapped[str | None] = mapped_column(String(30))
    session_score: Mapped[float | None] = mapped_column(Float)
    skill_scores: Mapped[str | None] = mapped_column(Text)
    skills_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    client_stamp: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class SkillPointLog(Base):
    __tablename__ = "skill_point_log"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50))
    user_code: Mapped[str | None] = mapped_column(String(30))
    courseware_key: Mapped[str | None] = mapped_column(String(30))
    courseware_code: Mapped[str] = mapped_column(String(30))
    course_code: Mapped[str | None] = mapped_column(String(30))
    dept_code: Mapped[str | None] = mapped_column(String(30))
    skills_count: Mapped[int | None] = mapped_column(Integer)
    step_score: Mapped[str | None] = mapped_column(Text)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    operated_at: Mapped[datetime | None] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class SkillErrorLog(Base):
    __tablename__ = "skill_error_log"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dept_code: Mapped[str | None] = mapped_column(String(30))
    user_id: Mapped[str] = mapped_column(String(50))
    user_code: Mapped[str | None] = mapped_column(String(30))
    course_code: Mapped[str | None] = mapped_column(String(30))
    courseware_code: Mapped[str | None] = mapped_column(String(30))
    step_index: Mapped[int | None] = mapped_column(Integer)
    step_score: Mapped[str | None] = mapped_column(String(20))
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    occurred_at: Mapped[datetime] = mapped_column(DateTime)
    client_stamp: Mapped[str | None] = mapped_column(String(50))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
