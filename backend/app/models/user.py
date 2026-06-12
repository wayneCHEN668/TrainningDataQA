from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class UserInfo(Base):
    __tablename__ = "user_info"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    user_code: Mapped[str | None] = mapped_column(String(30), unique=True)
    user_name: Mapped[str] = mapped_column(String(100))
    mobile: Mapped[str | None] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(100))
    role_level: Mapped[int] = mapped_column(Integer, default=3)
    dept_code: Mapped[str | None] = mapped_column(String(30))
    position_code: Mapped[str | None] = mapped_column(String(30))
    external_code: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class UserProfile(Base):
    __tablename__ = "user_profile"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    gender: Mapped[int | None] = mapped_column(Integer)
    education: Mapped[str | None] = mapped_column(String(30))
    job_title: Mapped[str | None] = mapped_column(String(50))
    position_code: Mapped[str | None] = mapped_column(String(30))
    birthday: Mapped[datetime | None] = mapped_column(Date)
    avatar_url: Mapped[str | None] = mapped_column(String(200))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
    biography: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class StudentClass(Base):
    __tablename__ = "student_class"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    class_code: Mapped[str] = mapped_column(String(30))


class TeacherDept(Base):
    __tablename__ = "teacher_dept"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    dept_code: Mapped[str] = mapped_column(String(30))
    role_type: Mapped[int] = mapped_column(Integer, default=0)


class TeacherClass(Base):
    __tablename__ = "teacher_class"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    class_code: Mapped[str] = mapped_column(String(30))
    role_type: Mapped[int] = mapped_column(Integer, default=1)
    subject: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class AdminDept(Base):
    __tablename__ = "admin_dept"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    dept_code: Mapped[str] = mapped_column(String(30), unique=True)
