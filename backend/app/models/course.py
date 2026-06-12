from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Course(Base):
    __tablename__ = "course"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_code: Mapped[str] = mapped_column(String(30), unique=True)
    course_name: Mapped[str] = mapped_column(String(200))
    course_desc: Mapped[str | None] = mapped_column(Text)
    category_code: Mapped[str | None] = mapped_column(String(30))
    dept_code: Mapped[str | None] = mapped_column(String(30))
    creator_id: Mapped[str | None] = mapped_column(String(50))
    credit: Mapped[int] = mapped_column(Integer, default=0)
    study_hours: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class Courseware(Base):
    __tablename__ = "courseware"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    courseware_code: Mapped[str] = mapped_column(String(30), unique=True)
    courseware_key: Mapped[str] = mapped_column(String(30), unique=True)
    courseware_name: Mapped[str] = mapped_column(String(100))
    type_code: Mapped[str] = mapped_column(String(20))
    skill_point_count: Mapped[int] = mapped_column(Integer, default=0)
    difficulty_level: Mapped[str | None] = mapped_column(String(20))
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    dept_code: Mapped[str | None] = mapped_column(String(30))
    creator_id: Mapped[str | None] = mapped_column(String(50))
    is_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    has_exam: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class CourseCategory(Base):
    __tablename__ = "course_category"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    category_code: Mapped[str] = mapped_column(String(30), unique=True)
    category_name: Mapped[str] = mapped_column(String(50))
    parent_code: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class CourseCourseware(Base):
    __tablename__ = "course_courseware"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_code: Mapped[str] = mapped_column(String(30))
    courseware_code: Mapped[str] = mapped_column(String(30))
    display_order: Mapped[int] = mapped_column(Integer, default=0)


class ClassCourse(Base):
    __tablename__ = "class_course"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    class_code: Mapped[str] = mapped_column(String(30))
    course_code: Mapped[str] = mapped_column(String(30))
    term_number: Mapped[int] = mapped_column(Integer)


class SkillPoint(Base):
    __tablename__ = "skill_point"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    courseware_key: Mapped[str] = mapped_column(String(50))
    step_index: Mapped[int] = mapped_column(Integer)
    score_name: Mapped[str | None] = mapped_column(String(200))
    score_config: Mapped[str | None] = mapped_column(Text)
