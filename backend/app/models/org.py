from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Org(Base):
    __tablename__ = "org"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    app_id: Mapped[str] = mapped_column(String(30))
    org_name: Mapped[str] = mapped_column(String(100))
    org_desc: Mapped[str | None] = mapped_column(Text)
    is_default: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class Department(Base):
    __tablename__ = "department"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dept_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    dept_name: Mapped[str] = mapped_column(String(100))
    org_code: Mapped[str] = mapped_column(String(30))
    dept_desc: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class Major(Base):
    __tablename__ = "major"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    major_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    major_name: Mapped[str] = mapped_column(String(100))
    dept_code: Mapped[str] = mapped_column(String(30))
    major_desc: Mapped[str | None] = mapped_column(Text)
    curriculum_code: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class ClassGroup(Base):
    __tablename__ = "class_group"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    class_name: Mapped[str] = mapped_column(String(100))
    major_code: Mapped[str] = mapped_column(String(30))
    enroll_year: Mapped[str | None] = mapped_column(String(10))
    class_desc: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class Position(Base):
    __tablename__ = "position"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    position_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    position_name: Mapped[str] = mapped_column(String(100))
    position_desc: Mapped[str | None] = mapped_column(String(200))
    org_code: Mapped[str] = mapped_column(String(30))
    scope_type: Mapped[int] = mapped_column(Integer)
    scope_code: Mapped[str] = mapped_column(String(30))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
