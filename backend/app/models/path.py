from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import DECIMAL
from app.models.base import Base


class LearnerProfile(Base):
    __tablename__ = "learner_profile"
    __table_args__ = {"keep_existing": True}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), unique=True)
    avg_session_minutes: Mapped[int] = mapped_column(Integer, default=0)
    preferred_time_slots: Mapped[str | None] = mapped_column(String(100))
    avg_weekly_study_days: Mapped[float] = mapped_column(DECIMAL(4, 2))
    avg_completion_rate: Mapped[float] = mapped_column(DECIMAL(5, 2))
    total_study_minutes: Mapped[int] = mapped_column(Integer, default=0)
    total_courses_completed: Mapped[int] = mapped_column(Integer, default=0)
    skill_scores: Mapped[dict | None] = mapped_column(JSON)
    strong_domains: Mapped[str | None] = mapped_column(Text)
    weak_domains: Mapped[str | None] = mapped_column(Text)
    avg_skill_error_rate: Mapped[float] = mapped_column(DECIMAL(5, 2))
    learning_style: Mapped[str | None] = mapped_column(String(20))
    study_pace: Mapped[str | None] = mapped_column(String(20))
    engagement_score: Mapped[float] = mapped_column(DECIMAL(5, 2))
    profile_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class LearningPath(Base):
    __tablename__ = "learning_path"
    __table_args__ = {"keep_existing": True}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    path_code: Mapped[str] = mapped_column(String(30), unique=True)
    path_name: Mapped[str] = mapped_column(String(200))
    target_position: Mapped[str | None] = mapped_column(String(50))
    source_type: Mapped[int] = mapped_column(Integer, default=0)
    org_code: Mapped[str | None] = mapped_column(String(30))
    estimated_days: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class PathNode(Base):
    __tablename__ = "path_node"
    __table_args__ = {"keep_existing": True}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    path_code: Mapped[str] = mapped_column(String(30))
    node_seq: Mapped[int] = mapped_column(Integer)
    course_code: Mapped[str] = mapped_column(String(30))
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    estimated_days: Mapped[int | None] = mapped_column(Integer)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class PathEnrollment(Base):
    __tablename__ = "path_enrollment"
    __table_args__ = {"keep_existing": True}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50))
    path_code: Mapped[str] = mapped_column(String(30))
    current_node_seq: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[int] = mapped_column(Integer, default=0)
    overall_progress: Mapped[float] = mapped_column(DECIMAL(5, 2))
    ai_predicted_done: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
