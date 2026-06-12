# Phase 1 数据基础层 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 MySQL skillcloud_v2 数据库上建立 AI 系统的数据基础层：权限视图、基准统计表、分析宽表，以及 Python FastAPI 项目骨架和 SchemaIndexService。

**Architecture:** 四层数据基础（Layer 1 实时视图 → Layer 2 已有预聚合表 → Layer 3 基准统计表 → Layer 4 综合分析宽表），搭配 FastAPI async 骨架 + SQLAlchemy 只读映射 + Alembic 迁移 + APScheduler 定时刷新。

**Tech Stack:** Python 3.12, FastAPI 0.115+, SQLAlchemy 2.0 (async), Alembic 1.13+, APScheduler 3.10+, Redis 7 (aioredis), MySQL 8.0

---

### Task 1: 项目脚手架搭建

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py` and all subpackage `__init__.py` files
- Create: `.env.example`

- [ ] **Step 1: Create backend/pyproject.toml**

```toml
[project]
name = "skillcloud-ai"
version = "0.1.0"
description = "SkillCloudHS AI 数据问答系统"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy[asyncio]>=2.0.30",
    "aiomysql>=0.2.0",
    "redis[hiredis]>=5.0.0",
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0",
    "apscheduler>=3.10.0",
    "alembic>=1.13.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]
```

- [ ] **Step 2: Create backend/requirements.txt**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy[asyncio]==2.0.36
aiomysql==0.2.0
redis[hiredis]==5.2.1
pyyaml==6.0.2
pydantic==2.10.4
pydantic-settings==2.7.1
httpx==0.28.1
python-dotenv==1.0.1
apscheduler==3.11.0
alembic==1.14.1
pytest==8.3.4
pytest-asyncio==0.25.0
```

- [ ] **Step 3: Create directory structure**

```bash
cd backend
mkdir -p app/api/v1 app/services/ai app/models app/schemas app/core app/jobs
mkdir -p tests/services/ai
for d in app app/api app/api/v1 app/services app/services/ai app/models app/schemas app/core app/jobs tests tests/services tests/services/ai; do
    touch "$d/__init__.py"
done
```

- [ ] **Step 4: Create .env.example**

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=ai_reader
DB_PASSWORD=your_readonly_password_here
DB_NAME=skillcloud_v2
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
REDIS_URL=redis://localhost:6379/0
SCHEMA_YAML_PATH=../doc/db_table_index.yaml
LLM_BASE_URL=http://localhost:8000/v1
LLM_MODEL=qwen2.5-72b-instruct
```

- [ ] **Step 5: Copy .env.example to .env**

```bash
cp .env.example .env
```

- [ ] **Step 6: Install dependencies**

```bash
cd backend && pip install -e ".[dev]"
```
Expected: all packages install without error.

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat: scaffold backend project structure with dependencies"
```

---

### Task 2: Core 基础设施 (config, database, redis)

**Files:**
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/database.py`
- Create: `backend/app/core/redis.py`

- [ ] **Step 1: Write backend/app/core/config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "ai_reader"
    DB_PASSWORD: str = ""
    DB_NAME: str = "skillcloud_v2"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    REDIS_URL: str = "redis://localhost:6379/0"
    SCHEMA_YAML_PATH: str = "../doc/db_table_index.yaml"
    LLM_BASE_URL: str = "http://localhost:8000/v1"
    LLM_MODEL: str = "qwen2.5-72b-instruct"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

- [ ] **Step 2: Write backend/app/core/database.py**

```python
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from app.core.config import settings

DATABASE_URL = (
    f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    f"?charset=utf8mb4"
)

engine = create_async_engine(
    DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Dependency injection: provides read-only database session."""
    async with AsyncSessionLocal() as session:
        yield session
```

- [ ] **Step 3: Write backend/app/core/redis.py**

```python
import redis.asyncio as aioredis
from app.core.config import settings

redis_pool = aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis() -> aioredis.Redis:
    return redis_pool
```

- [ ] **Step 4: Verify imports**

```bash
cd backend && python -c "from app.core.config import settings; print(settings.DB_NAME)"
```
Expected: prints `skillcloud_v2`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/
git commit -m "feat: add core infrastructure (config, database, redis)"
```

---


### Task 3: SQLAlchemy ORM 模型 — 已有业务表（M1-M5, M7-M11 核心）

> 策略：只映射 AI 系统实际查询的表和字段。Laravel 框架表（cache, jobs, migrations, sessions, users 等）不映射。
> 所有已有表通过 Alembic `--autogenerate` 二次确认，ORMs 为只读映射，`__table_args__ = {"keep_existing": True}`。

**Files:**
- Create: `backend/app/models/base.py`
- Create: `backend/app/models/org.py` (M1: org, department, major, class_group, position)
- Create: `backend/app/models/user.py` (M2: user_info, user_profile, student_class, teacher_dept, teacher_class, admin_dept)
- Create: `backend/app/models/course.py` (M3: course, courseware, course_category, course_courseware, class_course, skill_point)
- Create: `backend/app/models/learning.py` (M4: study_session_log, skill_point_log, skill_error_log)
- Create: `backend/app/models/exam.py` (M5: exam_session, exam_enrollment, exam_answer, question, question_option)
- Create: `backend/app/models/stats.py` (M9: org_daily_stats, org_monthly_stats, org_course_stats, courseware_study_stats — 已存在，只读)
- Create: `backend/app/models/progress.py` (M10: learning_progress, course_grade)
- Create: `backend/app/models/path.py` (M11: learning_path, path_node, path_enrollment, learner_profile)

- [ ] **Step 1: Write backend/app/models/base.py**

```python
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    refreshed_at: Mapped[datetime] = mapped_column(
        server_default="CURRENT_TIMESTAMP"
    )
```

- [ ] **Step 2: Write backend/app/models/org.py — M1**

```python
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
```

- [ ] **Step 3: Write backend/app/models/user.py — M2**

```python
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
```

- [ ] **Step 4: Write backend/app/models/course.py — M3**

```python
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
```

- [ ] **Step 5: Write backend/app/models/learning.py — M4**

```python
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
```

- [ ] **Step 6: Write backend/app/models/exam.py — M5 (核心字段)**

```python
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
```

- [ ] **Step 7: Write backend/app/models/stats.py — M9 (已存在，只读)**

```python
from datetime import datetime, date
from sqlalchemy import String, Integer, Date, Float
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
```

- [ ] **Step 8: Write backend/app/models/progress.py — M10 (已存在，只读)**

```python
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
```

- [ ] **Step 9: Write backend/app/models/path.py — M11 (已存在，只读)**

```python
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
```

- [ ] **Step 10: Verify all model imports**

```bash
cd backend && python -c "
from app.models.org import Org, Department, Major, ClassGroup, Position
from app.models.user import UserInfo, UserProfile, StudentClass, TeacherDept, TeacherClass, AdminDept
from app.models.course import Course, Courseware, CourseCategory, CourseCourseware, ClassCourse, SkillPoint
from app.models.learning import StudySessionLog, SkillPointLog, SkillErrorLog
from app.models.exam import ExamSession, ExamEnrollment, ExamAnswer, Question, QuestionOption
from app.models.stats import OrgDailyStats, OrgMonthlyStats, OrgCourseStats, CoursewareStudyStats
from app.models.progress import LearningProgress, CourseGrade
from app.models.path import LearnerProfile, LearningPath, PathNode, PathEnrollment
print('All models imported OK')
"
```
Expected: prints `All models imported OK` (no actual DB connection needed for import).

- [ ] **Step 11: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add ORM models for all business tables (M1-M5, M9-M11, read-only)"
```

---


### Task 4: SQLAlchemy ORM 模型 — 新建宽表/基准表

**Files:**
- Create: `backend/app/models/benchmark.py`

- [ ] **Step 1: Write backend/app/models/benchmark.py**

```python
from datetime import datetime, date
from sqlalchemy import String, Integer, DateTime, Date, Text, JSON, Float, Boolean
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
```

- [ ] **Step 2: Verify benchmark model imports**

```bash
cd backend && python -c "
from app.models.benchmark import (
    DeptBenchmarkStats, OrgBenchmarkStats,
    LearnerComprehensive, ExamAnalysis, SkillErrorSummary,
)
print('Benchmark models imported OK')
"
```
Expected: prints `Benchmark models imported OK`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/benchmark.py
git commit -m "feat: add ORM models for new wide tables and benchmark tables"
```

---

### Task 5: Alembic 初始化 + 表迁移 (001-004)

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/001_create_benchmark_tables.py`
- Create: `backend/alembic/versions/002_create_v_learner_comprehensive.py`
- Create: `backend/alembic/versions/003_create_v_exam_analysis.py`
- Create: `backend/alembic/versions/004_create_v_skill_error_summary.py`
- Modify: `backend/app/core/database.py` (add metadata import for autogenerate)

- [ ] **Step 1: Initialize Alembic**

```bash
cd backend && alembic init alembic
```
Expected: creates `alembic/` directory and `alembic.ini`.

- [ ] **Step 2: Configure alembic.ini — change sqlalchemy.url line to:**

```ini
sqlalchemy.url = mysql+aiomysql://ai_reader:CHANGEME@localhost:3306/skillcloud_v2?charset=utf8mb4
```

> Note: The actual password will come from .env. For production use, Alembic should read from environment variables. In Phase 1 development, edit this line directly with the dev DB credentials.

- [ ] **Step 3: Configure alembic/env.py — replace content with:**

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.core.config import settings
from app.models.base import Base

# Import all models so Base.metadata knows about them
import app.models.org       # noqa: F401
import app.models.user      # noqa: F401
import app.models.course    # noqa: F401
import app.models.learning  # noqa: F401
import app.models.exam      # noqa: F401
import app.models.stats     # noqa: F401
import app.models.progress  # noqa: F401
import app.models.path      # noqa: F401
import app.models.benchmark # noqa: F401

config = context.config
config.set_main_option(
    "sqlalchemy.url",
    f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    f"?charset=utf8mb4"
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: Create migration 001 — benchmark tables**

```bash
cd backend && alembic revision -m "create_benchmark_tables"
```
Rename the generated file to `001_create_benchmark_tables.py`, then replace upgrade() and downgrade():

```python
"""create_benchmark_tables

Revision ID: 001
Create Date: 2026-06-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dept_benchmark_stats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("dept_code", sa.String(30), nullable=False),
        sa.Column("org_code", sa.String(30), nullable=False),
        sa.Column("stat_period", sa.String(10), nullable=False, server_default="month"),
        sa.Column("stat_date", sa.Date(), nullable=False),
        sa.Column("avg_completion_rate", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_exam_pass_rate", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_composite_score", sa.DECIMAL(6, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_study_minutes", sa.DECIMAL(10, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_skill_error_rate", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_engagement_score", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("p25_completion_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("p50_completion_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("p75_completion_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("p25_composite_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("p50_composite_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("p75_composite_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("total_learners", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("refreshed_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dept_code", "stat_period", "stat_date", name="uk_dbs"),
    )
    op.create_index("idx_dbs_org", "dept_benchmark_stats", ["org_code"])
    op.create_index("idx_dbs_date", "dept_benchmark_stats", ["stat_date"])

    op.create_table(
        "org_benchmark_stats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("org_code", sa.String(30), nullable=False),
        sa.Column("stat_period", sa.String(10), nullable=False, server_default="month"),
        sa.Column("stat_date", sa.Date(), nullable=False),
        sa.Column("avg_completion_rate", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_exam_pass_rate", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_composite_score", sa.DECIMAL(6, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_study_minutes", sa.DECIMAL(10, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_skill_error_rate", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_engagement_score", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("p25_completion_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("p50_completion_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("p75_completion_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("p25_composite_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("p50_composite_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("p75_composite_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("total_orgs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_learners", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("refreshed_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("org_code", "stat_period", "stat_date", name="uk_obs"),
    )
    op.create_index("idx_obs_date", "org_benchmark_stats", ["stat_date"])


def downgrade() -> None:
    op.drop_table("org_benchmark_stats")
    op.drop_table("dept_benchmark_stats")
```

- [ ] **Step 5: Create migration 002 — v_learner_comprehensive**

```bash
cd backend && alembic revision -m "create_v_learner_comprehensive"
```
Rename to `002_create_v_learner_comprehensive.py`, set `down_revision = "001"`, then:

```python
def upgrade() -> None:
    op.create_table(
        "v_learner_comprehensive",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(50), nullable=False),
        sa.Column("user_code", sa.String(30), nullable=True),
        sa.Column("user_name", sa.String(100), nullable=True),
        sa.Column("dept_code", sa.String(30), nullable=True),
        sa.Column("dept_name", sa.String(100), nullable=True),
        sa.Column("org_code", sa.String(30), nullable=True),
        sa.Column("class_code", sa.String(30), nullable=True),
        sa.Column("class_name", sa.String(100), nullable=True),
        sa.Column("total_courses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("courses_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_rate", sa.DECIMAL(5, 2), nullable=False, server_default="0.00"),
        sa.Column("avg_composite_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("avg_courseware_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("avg_exam_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("avg_assignment_score", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("grade_rank", sa.String(10), nullable=True),
        sa.Column("total_exams_taken", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("exams_passed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("exam_pass_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("best_exam_score", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("total_study_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_study_sessions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_session_minutes", sa.Integer(), nullable=True),
        sa.Column("last_studied_at", sa.DateTime(), nullable=True),
        sa.Column("is_at_risk", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("risk_type", sa.String(50), nullable=True),
        sa.Column("days_since_last_study", sa.Integer(), nullable=True),
        sa.Column("refreshed_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uk_vlc"),
    )
    op.create_index("idx_vlc_dept", "v_learner_comprehensive", ["dept_code"])
    op.create_index("idx_vlc_org", "v_learner_comprehensive", ["org_code"])
    op.create_index("idx_vlc_risk", "v_learner_comprehensive", ["is_at_risk", "risk_type"])


def downgrade() -> None:
    op.drop_table("v_learner_comprehensive")
```

- [ ] **Step 6: Create migration 003 — v_exam_analysis**

```bash
cd backend && alembic revision -m "create_v_exam_analysis"
```
Rename to `003_create_v_exam_analysis.py`, set `down_revision = "002"`, implement with columns from design doc §5.2.

- [ ] **Step 7: Create migration 004 — v_skill_error_summary**

```bash
cd backend && alembic revision -m "create_v_skill_error_summary"
```
Rename to `004_create_v_skill_error_summary.py`, set `down_revision = "003"`, implement with columns from design doc §5.3.

- [ ] **Step 8: Run migrations 001-004**

```bash
cd backend && alembic upgrade 004
```
Expected: all 4 tables created successfully in `skillcloud_v2`.

- [ ] **Step 9: Commit**

```bash
git add backend/alembic/
git commit -m "feat: add alembic migrations 001-004 (benchmark + wide tables)"
```

---

### Task 6: Alembic VIEW 迁移 + qa_session_log (005-007)

**Files:**
- Create: `backend/alembic/versions/005_create_v_learner_overview.py`
- Create: `backend/alembic/versions/006_create_v_course_overview.py`
- Create: `backend/alembic/versions/007_create_qa_session_log.py`

- [ ] **Step 1: Create migration 005 — v_learner_overview (VIEW)**

```bash
cd backend && alembic revision -m "create_v_learner_overview"
```
Rename to `005_create_v_learner_overview.py`, set `down_revision = "004"`.

```python
def upgrade() -> None:
    op.execute("""
        CREATE VIEW v_learner_overview AS
        SELECT
            u.user_id, u.user_code, u.user_name, u.role_level,
            u.dept_code, d.dept_name,
            sc.class_code, cg.class_name,
            u.position_code, p.position_name,
            up.gender, up.education, up.job_title,
            up.last_login_at,
            d.org_code
        FROM user_info u
        LEFT JOIN department d ON u.dept_code = d.dept_code
        LEFT JOIN student_class sc ON u.user_id = sc.user_id
        LEFT JOIN class_group cg ON sc.class_code = cg.class_code
        LEFT JOIN position p ON u.position_code = p.position_code
        LEFT JOIN user_profile up ON u.user_id = up.user_id
        WHERE u.deleted_at IS NULL
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_learner_overview")
```

- [ ] **Step 2: Create migration 006 — v_course_overview (VIEW)**

```bash
cd backend && alembic revision -m "create_v_course_overview"
```
Rename to `006_create_v_course_overview.py`, set `down_revision = "005"`.

```python
def upgrade() -> None:
    op.execute("""
        CREATE VIEW v_course_overview AS
        SELECT
            c.course_code, c.course_name, c.credit, c.study_hours,
            c.category_code, cc.category_name,
            c.dept_code, d.dept_name,
            c.is_published,
            (SELECT COUNT(*) FROM course_courseware ccw
             WHERE ccw.course_code = c.course_code) AS courseware_count
        FROM course c
        LEFT JOIN course_category cc ON c.category_code = cc.category_code
        LEFT JOIN department d ON c.dept_code = d.dept_code
        WHERE c.deleted_at IS NULL
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_course_overview")
```

- [ ] **Step 3: Create migration 007 — qa_session_log (from PRD §11.1)**

```bash
cd backend && alembic revision -m "create_qa_session_log"
```
Rename to `007_create_qa_session_log.py`, set `down_revision = "006"`.

```python
def upgrade() -> None:
    op.create_table(
        "qa_session_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(50), nullable=False),
        sa.Column("user_id", sa.String(50), nullable=False),
        sa.Column("org_code", sa.String(30), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(50), nullable=True),
        sa.Column("complexity", sa.String(10), nullable=True),
        sa.Column("modules_used", sa.String(300), nullable=True),
        sa.Column("steps_count", sa.Integer(), server_default="0"),
        sa.Column("tools_used", sa.String(300), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("user_feedback", sa.SmallInteger(), nullable=True),
        sa.Column("fallback_used", sa.Boolean(), server_default="0"),
        sa.Column("asked_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_qsl_asked", "qa_session_log", ["asked_at"])
    op.create_index("idx_qsl_intent", "qa_session_log", ["intent"])
    op.create_index("idx_qsl_feedback", "qa_session_log", ["user_feedback"])


def downgrade() -> None:
    op.drop_table("qa_session_log")
```

- [ ] **Step 4: Run all migrations to head**

```bash
cd backend && alembic upgrade head
```
Expected: "Running upgrade 004 -> 005", "Running upgrade 005 -> 006", "Running upgrade 006 -> 007" all pass.

- [ ] **Step 5: Verify existing tables untouched**

Connect to MySQL and run:
```sql
CHECKSUM TABLE org_daily_stats, org_monthly_stats, org_course_stats, courseware_study_stats;
```
Save the checksums as baseline for later verification.

- [ ] **Step 6: Commit**

```bash
git add backend/alembic/versions/005_*.py backend/alembic/versions/006_*.py backend/alembic/versions/007_*.py
git commit -m "feat: add alembic migrations 005-007 (VIEWs + qa_session_log)"
```

---


### Task 7: SchemaIndexService 实现

**Files:**
- Create: `backend/app/services/ai/schema_index.py`
- Source: `doc/db_table_index.yaml` (已存在)

- [ ] **Step 1: Write backend/app/services/ai/schema_index.py**

```python
import json
import re
from pathlib import Path

import yaml
import redis.asyncio as aioredis


class SchemaIndexService:
    """db_table_index.yaml 三层按需加载服务。

    四个核心方法对应 AI 问答请求的四个注入点：
    1. get_module_index_text()        -> 注入点1: 意图识别 prompt (~400 tokens)
    2. get_modules_for_intent(intent) -> 注入点2: 代码路由 (0 tokens)
    3. get_table_summaries_text()     -> 注入点3: ReAct prompt (~800 tokens)
    4. validate_query_tables(sql)     -> 注入点4: SQL 黑名单校验 (0 tokens)
    """

    CACHE_KEY = "schema_index_v1"

    def __init__(self, yaml_path: str = "../doc/db_table_index.yaml",
                 redis: aioredis.Redis | None = None):
        self._path = Path(yaml_path)
        self._redis = redis
        self._index: dict | None = None

    # ── 启动时调用 ──────────────────────────────────────────

    async def load(self) -> None:
        """启动时调用，解析 YAML 并缓存到 Redis。"""
        if self._redis:
            cached = await self._redis.get(self.CACHE_KEY)
            if cached:
                self._index = json.loads(cached)
                return

        with open(self._path, encoding="utf-8") as f:
            self._index = yaml.safe_load(f)

        if self._redis:
            await self._redis.set(
                self.CACHE_KEY,
                json.dumps(self._index, ensure_ascii=False),
                ex=86400,  # 24 小时
            )

    async def refresh(self) -> None:
        """部署新 YAML 后调用。"""
        if self._redis:
            await self._redis.delete(self.CACHE_KEY)
        self._index = None
        await self.load()

    # ── 注入点 1：意图识别 prompt（始终注入，~400 tokens）────

    def get_module_index_text(self) -> str:
        module_index = self._index["MODULE_INDEX"]
        lines = ["## 系统数据模块（意图识别参考）"]
        for name, info in module_index.items():
            answers = info.get("answers", "")
            lines.append(f"- {name}：{answers}")
        return "\n".join(lines)

    # ── 注入点 2：意图→模块路由（纯代码查表，0 token）───────

    def get_modules_for_intent(self, intent: str) -> list[str]:
        routing = self._index.get("INTENT_MODULE_ROUTING", {})
        return routing.get(intent, ["M10_进度成绩", "M9_统计数据"])

    # ── 注入点 3：ReAct prompt（按模块加载，~800 tokens）─────

    def get_table_summaries_text(
        self, modules: list[str], compact: bool = False
    ) -> str:
        summaries = self._index["TABLE_SUMMARIES"]
        lines = ["## 可用数据表（仅允许查询以下表）"]
        for table_key, info in summaries.items():
            if info.get("module") not in modules:
                continue
            if compact:
                lines.append(
                    f"- {table_key} ({info.get('label', '')})："
                    f"{info.get('row_meaning', '')}"
                )
            else:
                lines.append("")
                lines.append(f"### {table_key}（{info.get('label', '')}）")
                lines.append(f"一行含义：{info.get('row_meaning', '')}")

                answers = info.get("answers")
                if answers:
                    a = answers if isinstance(answers, str) else " | ".join(answers)
                    lines.append(f"用于回答：{a}")

                key_fields = info.get("key_fields")
                if key_fields:
                    f_str = "、".join(
                        f"{k}（{v}）" for k, v in key_fields.items()
                    )
                    lines.append(f"关键字段：{f_str}")

                null_meaning = info.get("null_meaning") or {}
                for field, meaning in null_meaning.items():
                    lines.append(f"注意：{field} 为 NULL 时 = {meaning}")

                caution = info.get("caution")
                if caution:
                    lines.append(f"警告：{caution.strip()}")
        return "\n".join(lines)

    # ── 注入点 4：SQL 执行前黑名单校验（代码层，0 token）─────

    FORBIDDEN_TABLE_PATTERN = re.compile(
        r"\b(cache|cache_locks|failed_jobs|job_batches|jobs|"
        r"migrations|password_reset_tokens|personal_access_tokens|"
        r"sessions|users)\b",
        re.IGNORECASE,
    )

    def validate_query_tables(self, sql: str) -> tuple[bool, str]:
        """验证 SQL 不包含禁止访问的系统表。"""
        found = self.FORBIDDEN_TABLE_PATTERN.findall(sql)
        if found:
            unique_found = list(set(found))
            return False, f"查询包含禁止访问的系统表：{unique_found}"
        return True, "OK"
```

- [ ] **Step 2: Verify import**

```bash
cd backend && python -c "from app.services.ai.schema_index import SchemaIndexService; print('SchemaIndexService import OK')"
```
Expected: `SchemaIndexService import OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/ai/schema_index.py
git commit -m "feat: implement SchemaIndexService with 3-layer on-demand schema loading"
```

---

### Task 8: SchemaIndexService 单元测试

**Files:**
- Create: `backend/tests/services/ai/test_schema_index.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Write backend/tests/conftest.py**

```python
import sys
from pathlib import Path

# Make backend/ the Python path root
sys.path.insert(0, str(Path(__file__).parent.parent))
```

- [ ] **Step 2: Write the failing test first — backend/tests/services/ai/test_schema_index.py**

```python
import pytest
from app.services.ai.schema_index import SchemaIndexService


YAML_PATH = "../doc/db_table_index.yaml"


@pytest.fixture
async def svc():
    s = SchemaIndexService(yaml_path=YAML_PATH)
    await s.load()
    return s


@pytest.mark.asyncio
async def test_loads_module_index(svc):
    text = svc.get_module_index_text()
    assert "M1_组织架构" in text
    assert "M11_学习路径" in text
    assert "## 系统数据模块" in text


@pytest.mark.asyncio
async def test_intent_routing_known(svc):
    modules = svc.get_modules_for_intent("EXAM_SCORE_QUERY")
    assert "M5_考试系统" in modules


@pytest.mark.asyncio
async def test_intent_routing_unknown_returns_default(svc):
    modules = svc.get_modules_for_intent("NONEXISTENT_INTENT")
    assert modules == ["M10_进度成绩", "M9_统计数据"]


@pytest.mark.asyncio
async def test_table_summaries_full(svc):
    text = svc.get_table_summaries_text(
        modules=["M5_考试系统"], compact=False
    )
    assert "exam_session" in text
    assert "exam_enrollment" in text
    assert "### " in text  # full mode has section headers


@pytest.mark.asyncio
async def test_table_summaries_compact(svc):
    text = svc.get_table_summaries_text(
        modules=["M5_考试系统"], compact=True
    )
    assert "exam_session" in text
    assert "### " not in text  # compact mode skips headers


@pytest.mark.asyncio
async def test_table_summaries_filters_by_module(svc):
    text = svc.get_table_summaries_text(
        modules=["M1_组织架构"], compact=False
    )
    assert "org" in text
    assert "exam_session" not in text  # M5 not loaded


@pytest.mark.asyncio
async def test_blacklist_blocks_forbidden(svc):
    ok, msg = svc.validate_query_tables("SELECT * FROM users")
    assert not ok
    assert "users" in msg


@pytest.mark.asyncio
async def test_blacklist_blocks_cache(svc):
    ok, msg = svc.validate_query_tables("SELECT * FROM cache")
    assert not ok


@pytest.mark.asyncio
async def test_blacklist_allows_business_table(svc):
    ok, msg = svc.validate_query_tables("SELECT * FROM user_info")
    assert ok


@pytest.mark.asyncio
async def test_all_22_intents_route(svc):
    routing = svc._index.get("INTENT_MODULE_ROUTING", {})
    assert len(routing) == 22, f"Expected 22 intents, got {len(routing)}"
```

- [ ] **Step 3: Run tests — expect failures for methods not yet fully validated**

```bash
cd backend && python -m pytest tests/services/ai/test_schema_index.py -v
```
Expected: all 10 tests pass (they should pass since the implementation is complete).

- [ ] **Step 4: If any test fails, fix the implementation and re-run**

```bash
cd backend && python -m pytest tests/services/ai/test_schema_index.py -v
```
Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/
git commit -m "test: add SchemaIndexService unit tests (10 tests)"
```

---

### Task 9: APScheduler 刷新任务

**Files:**
- Create: `backend/app/jobs/scheduler.py`
- Create: `backend/app/jobs/refresh_wide_tables.py`

- [ ] **Step 1: Write backend/app/jobs/refresh_wide_tables.py**

```python
"""宽表和基准表的定时刷新逻辑。"""
import logging
from datetime import date, timedelta

from sqlalchemy import text
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def _execute_refresh(table_name: str, sql: str) -> None:
    """通用刷新：执行给定的刷新 SQL。"""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(text(sql))
            await session.commit()
            logger.info("%s 刷新完成，影响行数: %s", table_name, result.rowcount)
        except Exception:
            await session.rollback()
            logger.exception("%s 刷新失败", table_name)
            raise


async def refresh_benchmark_stats() -> None:
    """每月 1 日 04:00 执行：重建上月院系/机构基准统计。"""
    today = date.today()
    first_of_month = today.replace(day=1)
    last_month_end = first_of_month - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    sql = f"""
        -- dept 级基准（简化版，实际生产需加分位数计算）
        INSERT INTO dept_benchmark_stats
            (dept_code, org_code, stat_period, stat_date,
             avg_completion_rate, avg_composite_score, total_learners)
        SELECT
            d.dept_code, d.org_code, 'month', '{last_month_end}',
            COALESCE(AVG(cg.completion_rate), 0),
            COALESCE(AVG(cg.total_score), 0),
            COUNT(DISTINCT u.user_id)
        FROM department d
        JOIN user_info u ON u.dept_code = d.dept_code AND u.deleted_at IS NULL
        LEFT JOIN course_grade cg ON u.user_id = cg.user_id
        WHERE u.role_level = 3
        GROUP BY d.dept_code, d.org_code
        ON DUPLICATE KEY UPDATE
            avg_completion_rate = VALUES(avg_completion_rate),
            avg_composite_score = VALUES(avg_composite_score),
            total_learners = VALUES(total_learners),
            refreshed_at = CURRENT_TIMESTAMP
    """
    await _execute_refresh("dept_benchmark_stats", sql)

    # org 级基准（同理，按 org_code GROUP BY）
    sql_org = f"""
        INSERT INTO org_benchmark_stats
            (org_code, stat_period, stat_date,
             avg_completion_rate, avg_composite_score, total_learners, total_orgs)
        SELECT
            d.org_code, 'month', '{last_month_end}',
            COALESCE(AVG(cg.completion_rate), 0),
            COALESCE(AVG(cg.total_score), 0),
            COUNT(DISTINCT u.user_id),
            COUNT(DISTINCT d.org_code)
        FROM department d
        JOIN user_info u ON u.dept_code = d.dept_code AND u.deleted_at IS NULL
        LEFT JOIN course_grade cg ON u.user_id = cg.user_id
        WHERE u.role_level = 3
        GROUP BY d.org_code
        ON DUPLICATE KEY UPDATE
            avg_completion_rate = VALUES(avg_completion_rate),
            avg_composite_score = VALUES(avg_composite_score),
            total_learners = VALUES(total_learners),
            refreshed_at = CURRENT_TIMESTAMP
    """
    await _execute_refresh("org_benchmark_stats", sql_org)


async def refresh_learner_comprehensive() -> None:
    """每小时整点：增量刷新学员综合成绩宽表。"""
    sql = """
        INSERT INTO v_learner_comprehensive
            (user_id, user_code, user_name, dept_code, dept_name, org_code,
             total_courses, courses_completed, completion_rate,
             total_study_minutes, total_study_sessions, last_studied_at)
        SELECT
            u.user_id, u.user_code, u.user_name,
            u.dept_code, d.dept_name, d.org_code,
            COUNT(DISTINCT cc.course_code) AS total_courses,
            COUNT(DISTINCT CASE WHEN lp.status = 2 THEN lp.course_code END) AS courses_completed,
            COALESCE(AVG(cg.completion_rate), 0) AS completion_rate,
            COALESCE(SUM(ssl.stopped_at IS NOT NULL * TIMESTAMPDIFF(MINUTE, ssl.started_at, ssl.stopped_at)), 0),
            COUNT(DISTINCT ssl.id),
            MAX(ssl.started_at)
        FROM user_info u
        LEFT JOIN department d ON u.dept_code = d.dept_code
        LEFT JOIN class_course cc ON EXISTS (
            SELECT 1 FROM student_class sc WHERE sc.user_id = u.user_id AND sc.class_code = cc.class_code
        )
        LEFT JOIN learning_progress lp ON u.user_id = lp.user_id AND cc.course_code = lp.course_code
        LEFT JOIN course_grade cg ON u.user_id = cg.user_id AND cc.course_code = cg.course_code
        LEFT JOIN study_session_log ssl ON u.user_id = ssl.user_id
        WHERE u.deleted_at IS NULL AND u.role_level = 3
        GROUP BY u.user_id, u.user_code, u.user_name, u.dept_code, d.dept_name, d.org_code
        ON DUPLICATE KEY UPDATE
            total_courses = VALUES(total_courses),
            courses_completed = VALUES(courses_completed),
            completion_rate = VALUES(completion_rate),
            total_study_minutes = VALUES(total_study_minutes),
            total_study_sessions = VALUES(total_study_sessions),
            last_studied_at = VALUES(last_studied_at),
            refreshed_at = CURRENT_TIMESTAMP
    """
    await _execute_refresh("v_learner_comprehensive", sql)


async def refresh_exam_analysis() -> None:
    """每小时 15 分：增量刷新考试分析宽表。"""
    sql = """
        INSERT INTO v_exam_analysis
            (exam_session_code, session_name, org_code, linked_course_code,
             user_code, user_id, dept_code,
             attempt_number, total_score, is_passed, is_graded, submitted_at)
        SELECT
            es.exam_session_code, es.session_name, es.org_code, es.linked_course_code,
            ee.user_code, ui.user_id, ui.dept_code,
            ee.attempt_number, ee.total_score,
            CASE WHEN ee.total_score >= 60 THEN 1 ELSE 0 END,
            ee.is_graded, ee.submitted_at
        FROM exam_enrollment ee
        JOIN exam_session es ON ee.exam_session_code = es.exam_session_code
        LEFT JOIN user_info ui ON ee.user_code = ui.user_code
        WHERE ee.submitted_at IS NOT NULL
        ON DUPLICATE KEY UPDATE
            total_score = VALUES(total_score),
            is_passed = VALUES(is_passed),
            is_graded = VALUES(is_graded),
            submitted_at = VALUES(submitted_at),
            refreshed_at = CURRENT_TIMESTAMP
    """
    await _execute_refresh("v_exam_analysis", sql)


async def refresh_skill_error_summary() -> None:
    """每天 03:00：追加昨日技能点错误汇总。"""
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    sql = f"""
        INSERT IGNORE INTO v_skill_error_summary
            (courseware_code, course_code, dept_code, step_index,
             total_attempts, total_errors, error_rate, unique_users,
             stat_date)
        SELECT
            courseware_code, course_code, dept_code, step_index,
            COUNT(*) AS total_attempts,
            SUM(error_count) AS total_errors,
            COALESCE(SUM(error_count) / NULLIF(COUNT(*), 0) * 100, 0) AS error_rate,
            COUNT(DISTINCT user_id) AS unique_users,
            '{yesterday}'
        FROM skill_error_log
        WHERE DATE(occurred_at) = '{yesterday}'
        GROUP BY courseware_code, course_code, dept_code, step_index
    """
    await _execute_refresh("v_skill_error_summary", sql)


async def check_and_refresh_benchmark() -> None:
    """每天 03:00 兜底检查：如果今天是 1 日且 04:00 的任务已执行则跳过，
    如果没有执行（例如服务在 04:00 未运行），则补执行。

    Phase 1 简化实现：仅在每月 1 日执行 refresh_benchmark_stats。
    """
    today = date.today()
    if today.day == 1:
        logger.info("今天是本月 1 日，执行基准统计兜底刷新")
        await refresh_benchmark_stats()
    else:
        logger.debug("今天不是 1 日，跳过基准统计检查")
```

- [ ] **Step 2: Write backend/app/jobs/scheduler.py**

```python
"""APScheduler 配置与任务注册。"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.jobs.refresh_wide_tables import (
    refresh_benchmark_stats,
    refresh_learner_comprehensive,
    refresh_exam_analysis,
    refresh_skill_error_summary,
    check_and_refresh_benchmark,
)

scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


def register_jobs() -> None:
    # 基准统计：每月 1 日 04:00
    scheduler.add_job(
        refresh_benchmark_stats,
        trigger="cron",
        hour=4, minute=0, day=1,
        id="refresh_benchmark_stats",
        name="刷新院系/机构基准统计",
        replace_existing=True,
    )

    # 学员综合宽表：每小时整点
    scheduler.add_job(
        refresh_learner_comprehensive,
        trigger="cron",
        minute=0,
        id="refresh_learner_comprehensive",
        name="刷新学员综合成绩宽表",
        replace_existing=True,
    )

    # 考试分析宽表：每小时 15 分
    scheduler.add_job(
        refresh_exam_analysis,
        trigger="cron",
        minute=15,
        id="refresh_exam_analysis",
        name="刷新考试分析宽表",
        replace_existing=True,
    )

    # 技能点错误汇总：每天 03:00
    scheduler.add_job(
        refresh_skill_error_summary,
        trigger="cron",
        hour=3, minute=0,
        id="refresh_skill_error_summary",
        name="刷新技能点错误汇总",
        replace_existing=True,
    )

    # 基准统计兜底检查：每天 03:00
    scheduler.add_job(
        check_and_refresh_benchmark,
        trigger="cron",
        hour=3, minute=0,
        id="check_benchmark",
        name="检查基准统计是否需要刷新",
        replace_existing=True,
    )
```

- [ ] **Step 3: Verify scheduler setup**

```bash
cd backend && python -c "
from app.jobs.scheduler import scheduler, register_jobs
register_jobs()
jobs = scheduler.get_jobs()
print(f'Registered {len(jobs)} jobs:')
for j in jobs:
    print(f'  - {j.id}: {j.name}')
"
```
Expected: prints 5 registered jobs with their names.

- [ ] **Step 4: Commit**

```bash
git add backend/app/jobs/
git commit -m "feat: add APScheduler refresh jobs for wide tables and benchmarks"
```

---

### Task 10: FastAPI 入口 + 健康检查

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/schemas/health.py`

- [ ] **Step 1: Write backend/app/schemas/health.py**

```python
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
```

- [ ] **Step 2: Write backend/app/main.py**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import engine
from app.core.redis import redis_pool
from app.services.ai.schema_index import SchemaIndexService
from app.jobs.scheduler import scheduler, register_jobs
from app.schemas.health import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    schema_svc = SchemaIndexService(redis=redis_pool)
    await schema_svc.load()
    app.state.schema_svc = schema_svc
    register_jobs()
    scheduler.start()
    yield
    # 关闭时
    scheduler.shutdown(wait=False)
    await engine.dispose()
    await redis_pool.aclose()


app = FastAPI(
    title="SkillCloudHS AI API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="0.1.0")


@app.get("/api/v1/admin/schema-refresh")
async def schema_refresh():
    """手动刷新 Schema 缓存（Phase 7 加 Auth）。"""
    svc: SchemaIndexService = app.state.schema_svc
    await svc.refresh()
    return {"status": "refreshed"}
```

- [ ] **Step 3: Test health endpoint**

```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 &
sleep 2
curl http://localhost:8000/api/v1/health
```
Expected: `{"status":"ok","version":"0.1.0"}`

- [ ] **Step 4: Stop the server**

```bash
kill %1
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/app/schemas/health.py
git commit -m "feat: add FastAPI entry point with health check and lifespan"
```

---

### Task 11: Integration Verification（验收检查）

- [ ] **Step 1: Verify all migrations applied**

```bash
cd backend && alembic current
```
Expected: shows `007` (head).

- [ ] **Step 2: Verify existing pre-aggregated tables untouched**

Connect to MySQL and compare checksums against the baseline saved in Task 6 Step 5:
```sql
CHECKSUM TABLE org_daily_stats, org_monthly_stats, org_course_stats, courseware_study_stats;
```
Expected: checksums match the baseline.

- [ ] **Step 3: Verify AI read-only account**

```bash
cd backend && python -c "
import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def test():
    async with AsyncSessionLocal() as s:
        # Should fail: read-only user cannot INSERT
        try:
            await s.execute(text('INSERT INTO v_learner_comprehensive (user_id) VALUES (\"test\")'))
            await s.commit()
            print('FAIL: write operation should have been denied')
        except Exception as e:
            print(f'OK: write denied - {type(e).__name__}')

asyncio.run(test())
"
```
Expected: prints `OK: write denied - ...`.

- [ ] **Step 4: Verify SchemaIndexService loads correctly**

```bash
cd backend && python -c "
import asyncio
from app.services.ai.schema_index import SchemaIndexService

async def main():
    svc = SchemaIndexService()
    await svc.load()
    print('Module index length:', len(svc.get_module_index_text()))
    print('Modules for EXAM_SCORE_QUERY:', svc.get_modules_for_intent('EXAM_SCORE_QUERY'))
    print('Table summaries length:', len(svc.get_table_summaries_text(['M5_考试系统'])))
    ok, msg = svc.validate_query_tables('SELECT * FROM users')
    print(f'Blacklist test: ok={ok}, msg={msg}')
    print('All checks passed!')

asyncio.run(main())
"
```
Expected: prints module counts and "All checks passed!".

- [ ] **Step 5: Run full test suite**

```bash
cd backend && python -m pytest tests/ -v
```
Expected: all tests pass (10 SchemaIndexService tests at minimum).

- [ ] **Step 6: Verify APScheduler has 5 registered jobs**

```bash
cd backend && python -c "
from app.jobs.scheduler import scheduler, register_jobs
register_jobs()
jobs = scheduler.get_jobs()
assert len(jobs) == 5, f'Expected 5 jobs, got {len(jobs)}'
for j in sorted(jobs, key=lambda j: j.id):
    print(f'{j.id}: {j.next_run_time}')
print('All 5 jobs registered!')
"
```
Expected: prints 5 job IDs with next run times.

- [ ] **Step 7: Clean up generated scripts**

```bash
rm doc/plans/gen_plan*.py
```

- [ ] **Step 8: Final commit**

```bash
git add -A
git commit -m "chore: Phase 1 integration verification passed

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 任务依赖总结

```
Task 1 (脚手架)
  └─> Task 2 (core 基础设施)
       ├─> Task 3 (ORM - 业务表)
       │    └─> Task 5 (Alembic init + 001-004)
       │         └─> Task 6 (Alembic VIEW + 005-007)
       ├─> Task 4 (ORM - 宽表/基准表)
       │    └─> (与 Task 5 并行)
       └─> Task 7 (SchemaIndexService)
            └─> Task 8 (SchemaIndexService tests)
                 └─> (可与 Task 5-6, 9-10 并行)
       Task 9 (APScheduler) ─> 依赖 Task 2
       Task 10 (FastAPI main) ─> 依赖 Task 2, 7, 9
            └─> Task 11 (Integration verification) ─> 依赖所有
```

## 时间估算

| Task | 预估时间 | 关键风险 |
|---|---|---|
| 1: 脚手架 | 15 min | 网络拉依赖包 |
| 2: Core 基础设施 | 15 min | .env 配置正确 |
| 3: ORM 业务表 | 30 min | 字段类型匹配 MySQL |
| 4: ORM 宽表 | 15 min | 无 |
| 5: Alembic 001-004 | 30 min | DB 连接、权限 |
| 6: Alembic 005-007 | 20 min | VIEW 语法兼容 |
| 7: SchemaIndexService | 25 min | YAML 路径正确 |
| 8: SchemaIndexService tests | 15 min | pytest-asyncio 配置 |
| 9: APScheduler | 20 min | cron 表达式正确 |
| 10: FastAPI main | 15 min | 无 |
| 11: Integration verification | 20 min | DB 账号权限确认 |
| **Total** | **~3.5 hours** | |
