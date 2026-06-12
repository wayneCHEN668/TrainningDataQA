from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import DECIMAL
from app.models.base import Base


class ExamSession(Base):
    __tablename__ = "exam_session"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    exam_session_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    session_name: Mapped[str] = mapped_column(String(200))
    open_at: Mapped[datetime | None] = mapped_column(DateTime)
    close_at: Mapped[datetime | None] = mapped_column(DateTime)
    time_limit_seconds: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(Integer, default=0)
    grading_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    linked_course_code: Mapped[str | None] = mapped_column(String(30))
    org_code: Mapped[str | None] = mapped_column(String(30))
    creator_code: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class ExamEnrollment(Base):
    __tablename__ = "exam_enrollment"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    exam_session_code: Mapped[str] = mapped_column(String(30))
    user_code: Mapped[str] = mapped_column(String(30))
    assigned_paper_key: Mapped[str | None] = mapped_column(String(50))
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    total_score: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    is_graded: Mapped[bool] = mapped_column(Boolean, default=False)
    result_published: Mapped[bool] = mapped_column(Boolean, default=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class ExamAnswer(Base):
    __tablename__ = "exam_answer"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    enrollment_id: Mapped[int] = mapped_column(Integer)
    question_code: Mapped[str] = mapped_column(String(50))
    answer_content: Mapped[str | None] = mapped_column(Text)
    earned_score: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    grading_status: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class Question(Base):
    __tablename__ = "question"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    type_code: Mapped[str] = mapped_column(String(10))
    question_content: Mapped[str | None] = mapped_column(Text)
    content_plain: Mapped[str | None] = mapped_column(Text)
    difficulty_level: Mapped[int] = mapped_column(Integer, default=0)
    grading_type: Mapped[bool] = mapped_column(Boolean, default=False)
    org_code: Mapped[str | None] = mapped_column(String(30))
    is_disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class QuestionOption(Base):
    __tablename__ = "question_option"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    option_index: Mapped[int] = mapped_column(Integer)
    question_code: Mapped[str] = mapped_column(String(50))
    option_content: Mapped[str | None] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
