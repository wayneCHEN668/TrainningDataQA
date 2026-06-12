# Phase 4 工具集 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现 13 个 LangChain StructuredTool + QueryExecutor 权限注入 + PermissionScope，为 Phase 5 ReAct 引擎提供数据查询能力。

**Architecture:** QueryExecutor 使用 SQLAlchemy Core select() 构建查询，自动注入权限 WHERE 条件，执行前过黑名单校验。13 个工具由 ToolRegistry 注册为 LangChain StructuredTool。

**Tech Stack:** Python 3.12, SQLAlchemy 2.0 (Core), LangChain 0.3+, Pydantic v2, aiomysql

---

### Task 1: LangChain 依赖 + PermissionScope

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/app/services/query/__init__.py`
- Create: `backend/app/services/query/permission_scope.py`

- [ ] **Step 1: Add LangChain deps to pyproject.toml**

Add to `[project] dependencies`:
```
"langchain>=0.3.0",
"langchain-core>=0.3.0",
"langchain-openai>=0.2.0",
```

```bash
cd backend && pip install -e ".[dev]"
```

- [ ] **Step 2: Create backend/app/services/query/__init__.py**

Empty file.

- [ ] **Step 3: Write backend/app/services/query/permission_scope.py**

```python
"""Permission scope calculation from UserContext."""
from app.schemas.auth import UserContext


class PermissionScope:
    """Calculate WHERE filter conditions based on user role.

    Rules (QueryExecutor injects the first matching column):
      role_level=0 superadmin -> no filter
      role_level=1 admin     -> WHERE org_code = ?
      role_level=2 teacher   -> WHERE dept_code = ?
      role_level=3 student   -> WHERE user_id = ?
    """

    def __init__(self, user_ctx: UserContext):
        self.role_level = user_ctx.role_level
        self.user_id = user_ctx.user_id
        self.dept_code = user_ctx.dept_code

    @property
    def is_superadmin(self) -> bool:
        return self.role_level == 0

    def get_filters(self) -> list[tuple[str, str]]:
        """Return [(column_name, value), ...] in priority order.
        QueryExecutor picks the first column that exists in the queried table.
        """
        if self.role_level == 0:
            return []
        elif self.role_level == 1:
            # Admin: filter by org_code. Need to resolve org from dept.
            return [("org_code", self.dept_code)]
        elif self.role_level == 2:
            return [("dept_code", self.dept_code)]
        else:
            return [("user_id", self.user_id)]
```

- [ ] **Step 4: Verify import**

```bash
cd backend && python -c "
from app.services.query.permission_scope import PermissionScope
from app.schemas.auth import UserContext
ctx = UserContext(user_id='u1', user_code='s1', user_name='Student', role_level=3, dept_code='D1')
scope = PermissionScope(ctx)
assert scope.get_filters() == [('user_id', 'u1')]
print('PermissionScope OK')
"
```

- [ ] **Step 5: Commit**

---

### Task 2: QueryExecutor

**Files:**
- Create: `backend/app/services/query/query_executor.py`

- [ ] **Step 1: Write backend/app/services/query/query_executor.py**

```python
"""Query execution layer with automatic permission injection and blacklist validation."""
from sqlalchemy import Select
from sqlalchemy.sql import column as get_column
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import UserContext
from app.services.query.permission_scope import PermissionScope
from app.services.ai.schema_index import SchemaIndexService


class QueryExecutor:
    """Unified query execution layer for all tool functions.

    Three responsibilities:
    1. Auto-inject permission WHERE clause (hard constraint)
    2. Blacklist table name validation (hard constraint)
    3. Execute SQLAlchemy Core select() -> return list[dict]
    """

    def __init__(
        self,
        db: AsyncSession,
        user_ctx: UserContext,
        schema_svc: SchemaIndexService,
    ):
        self._db = db
        self._scope = PermissionScope(user_ctx)
        self._schema = schema_svc

    async def execute(self, stmt: Select) -> list[dict]:
        """Execute query with automatic permission injection + blacklist validation."""
        stmt = self._inject_permission(stmt)
        self._validate_tables(stmt)
        result = await self._db.execute(stmt)
        return [dict(row) for row in result.mappings()]

    def _inject_permission(self, stmt: Select) -> Select:
        if self._scope.is_superadmin:
            return stmt
        from_clause = stmt.get_final_froms()[0]
        available_columns = {c.name for c in from_clause.columns}
        for col_name, value in self._scope.get_filters():
            if col_name in available_columns:
                if isinstance(value, list):
                    return stmt.where(get_column(col_name).in_(value))
                return stmt.where(get_column(col_name) == value)
        return stmt  # No permission column in table -> allow (e.g., dictionary tables)

    def _validate_tables(self, stmt: Select) -> None:
        # Convert SELECT to SQL string for blacklist check
        compiled = stmt.compile(compile_kwargs={"literal_binds": True})
        ok, msg = self._schema.validate_query_tables(str(compiled))
        if not ok:
            raise PermissionError(msg)
```

- [ ] **Step 2: Verify import**

```bash
cd backend && python -c "
from app.services.query.query_executor import QueryExecutor
print('QueryExecutor import OK')
"
```

- [ ] **Step 3: Commit**

---

### Task 3: Pydantic Input 模型（16 个）

**Files:**
- Create: `backend/app/schemas/tools.py`

- [ ] **Step 1: Write backend/app/schemas/tools.py**

```python
"""Pydantic input models for all 16 tools (13 registered + 3 pure-LLM)."""
from pydantic import BaseModel, Field


# -- Q1: query_completion_rate --
class CompletionRateInput(BaseModel):
    scope_type: str = Field(description="all/org/dept/class/individual")
    time_start: str = Field(description="YYYY-MM-DD")
    time_end: str = Field(description="YYYY-MM-DD")
    course_code: str | None = Field(default=None)
    group_by: str = Field(default="none", description="none/dept/class/course")


# -- Q2: query_incomplete_learners --
class IncompleteLearnersInput(BaseModel):
    scope_type: str = Field(description="all/org/dept/class")
    course_code: str = Field(description="Course code to check")
    urgency_threshold_days: int = Field(default=7, description="Days before deadline to mark as urgent")


# -- Q3: query_exam_performance --
class ExamPerformanceInput(BaseModel):
    scope_type: str = Field(description="all/org/dept/class")
    exam_session_code: str | None = Field(default=None)
    time_start: str | None = Field(default=None)
    time_end: str | None = Field(default=None)
    group_by: str = Field(default="none", description="none/dept/exam")


# -- Q4: query_skill_error_analysis --
class SkillErrorInput(BaseModel):
    courseware_code: str = Field(description="Courseware code to analyze")
    top_n: int = Field(default=10, ge=1, le=50)


# -- Q5: query_learning_trend --
class LearningTrendInput(BaseModel):
    scope_type: str = Field(description="all/org/dept")
    metric: str = Field(description="study_minutes/completions/exam_pass/active_users")
    time_start: str = Field(description="YYYY-MM-DD")
    time_end: str = Field(description="YYYY-MM-DD")
    granularity: str = Field(default="week", description="day/week/month")


# -- Q6: query_at_risk_learners --
class AtRiskLearnersInput(BaseModel):
    scope_type: str = Field(description="all/org/dept/class")
    risk_types: list[str] = Field(default=["inactive", "low_score", "near_deadline"])


# -- Q7: query_individual_profile --
class IndividualProfileInput(BaseModel):
    user_code: str = Field(description="Student/staff code to look up")


# -- Q8: query_org_overview --
class OrgOverviewInput(BaseModel):
    time_start: str = Field(description="YYYY-MM-DD")
    time_end: str = Field(description="YYYY-MM-DD")


# -- C1: compute_period_comparison --
class PeriodComparisonInput(BaseModel):
    data_current: list[dict] = Field(description="Current period data points")
    data_previous: list[dict] = Field(description="Previous period data points")
    key_field: str = Field(description="Field name to compare (e.g., completion_rate)")


# -- C2: detect_anomalies --
class AnomalyDetectionInput(BaseModel):
    data_points: list[dict] = Field(description="Time series: [{date, value}]")
    threshold_sigma: float = Field(default=2.0, ge=0.5, le=5.0)


# -- C3: evaluate_metric_level --
class MetricLevelInput(BaseModel):
    metric_value: float = Field(description="The metric value to evaluate")
    benchmark_value: float = Field(description="Average benchmark for comparison")
    percentile_bands: dict | None = Field(default=None, description="{p25, p50, p75}")


# -- A1: get_benchmark --
class BenchmarkInput(BaseModel):
    scope_type: str = Field(description="dept/org")
    scope_code: str = Field(description="Dept or org code")
    stat_period: str = Field(default="month", description="month/quarter/year")


# -- A2: search_course_or_exam --
class SearchCourseExamInput(BaseModel):
    query: str = Field(description="Fuzzy course or exam name to search")
    search_type: str = Field(default="all", description="course/exam/all")
```

- [ ] **Step 2: Verify**

```bash
cd backend && python -c "
from app.schemas.tools import CompletionRateInput, ExamPerformanceInput
i = CompletionRateInput(scope_type='all', time_start='2026-01-01', time_end='2026-06-01')
print('Input model OK:', i.model_dump())
"
```

- [ ] **Step 3: Commit**

---

### Task 4: QueryExecutor 单元测试

**Files:**
- Create: `backend/tests/services/query/__init__.py`
- Create: `backend/tests/services/query/test_permission_scope.py`
- Create: `backend/tests/services/query/test_query_executor.py`

- [ ] **Step 1: Create test directory**

```bash
mkdir -p backend/tests/services/query
touch backend/tests/services/query/__init__.py
```

- [ ] **Step 2: Write backend/tests/services/query/test_permission_scope.py** (4 tests: superadmin, admin, teacher, student)

- [ ] **Step 3: Write backend/tests/services/query/test_query_executor.py** (4 tests: inject_permission by role, blacklist reject/allow)

- [ ] **Step 4: Run tests** → 8 tests pass

- [ ] **Step 5: Commit**

---

### Task 5: ToolRegistry + 13 工具

**Files:**
- Create: `backend/app/services/query/tool_registry.py`

This is the largest file (~500 lines). It contains:
- `ToolRegistry` class
- 13 `_make_*` methods, each returning a `StructuredTool`
- 3 compute-type tools as plain async functions

Each tool follows the pattern:
1. Build SQLAlchemy Core select() from wide table/ORM table
2. Call `self._executor.execute(stmt)`
3. Aggregate/format results into dict
4. Return dict

- [ ] **Step 1: Write the complete tool_registry.py**

Read the design doc for all 13 tool specifications. Key implementation notes:
- Q1-Q8: query wide tables via QueryExecutor
- C1-C3: pure Python, no DB
- A1-A2: query benchmark tables and course/exam tables

- [ ] **Step 2: Verify tool registration**

```bash
cd backend && python -c "
from app.services.query.tool_registry import ToolRegistry
print('ToolRegistry import OK')
"
```

- [ ] **Step 3: Commit**

---

### Task 6: ToolRegistry 单元测试

**Files:**
- Create: `backend/tests/services/query/test_tool_registry.py`

- [ ] **Step 1: Write tests** (~4 tests: 13 tools registered, unique names, each has args_schema, compute tools work)

- [ ] **Step 2: Run all tests**

```bash
cd backend && python -m pytest tests/services/query/ -v
```
Expected: 12+ tests pass.

- [ ] **Step 3: Commit**

---

### Task 7: 计算型工具单元测试

**Files:**
- Create: `backend/tests/services/query/test_compute_tools.py`

- [ ] **Step 1: Write tests**

```python
# test_period_comparison
current = [{"completion_rate": 80}, {"completion_rate": 90}]
previous = [{"completion_rate": 70}, {"completion_rate": 85}]
# Expected: avg_current=85, avg_previous=77.5, delta=+7.5, delta_pct=+9.68%

# test_anomaly_detection
points = [{"date": "2026-01-01", "value": 80}, ..., {"date": "2026-01-10", "value": 30}]
# Expected: value 30 flagged as anomaly (sigma > 2.0)

# test_metric_level_evaluate
# value=85, benchmark=70, p25=60, p50=75, p75=85 -> "excellent"
# value=50, benchmark=70 -> "below"
```

- [ ] **Step 2: Run** → 3 tests pass

- [ ] **Step 3: Commit**

---

### Task 8: 集成验证

- [ ] **Step 1: Run full test suite**

```bash
cd backend && python -m pytest tests/ -v
```

- [ ] **Step 2: Verify all imports**

```bash
cd backend && python -c "
from app.services.query.permission_scope import PermissionScope
from app.services.query.query_executor import QueryExecutor
from app.services.query.tool_registry import ToolRegistry
from app.schemas.tools import CompletionRateInput, ExamPerformanceInput
print('All Phase 4 imports OK')
"
```

- [ ] **Step 3: Verify tool count**

```python
# ToolRegistry should register exactly 13 tools
```

- [ ] **Step 4: Remove generator and commit**

---

## Task Dependencies

```
Task 1 (deps + PermissionScope)
  └─> Task 2 (QueryExecutor)
       └─> Task 5 (ToolRegistry)

Task 3 (Input models) ─> independent, can run parallel with 1-2

Task 4 (PermissionScope/QueryExecutor tests) ─> after Task 2
Task 6 (ToolRegistry tests) ─> after Task 5
Task 7 (Compute tools tests) ─> after Task 5

Task 8 (Verification) ─> after all
```

## Time Estimate

| Task | Time |
|------|------|
| 1: deps + PermissionScope | 10 min |
| 2: QueryExecutor | 15 min |
| 3: Input models (16 Pydantic) | 15 min |
| 4: Permission/Executor tests | 15 min |
| 5: ToolRegistry (13 tools) | 45 min |
| 6: ToolRegistry tests | 15 min |
| 7: Compute tools tests | 10 min |
| 8: Verification | 10 min |
| **Total** | **~2.25 hours** |
