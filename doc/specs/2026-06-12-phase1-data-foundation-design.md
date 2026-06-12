# Phase 1 — 数据基础层设计文档

**项目**: SkillCloudHS AI 数据问答系统  
**日期**: 2026-06-12  
**状态**: 已确认（待用户评审）

---

## 1. 概述

Phase 1 的目标是在现有 MySQL 8.0 `skillcloud_v2` 数据库之上建立 AI 系统的数据基础层，包括：权限过滤视图、基准统计表、综合分析宽表，以及 Python FastAPI 项目骨架和 SchemaIndexService。

### 1.1 关键约束

- 现有预聚合统计表（`org_daily_stats`、`org_monthly_stats`、`org_course_stats`、`courseware_study_stats`）**只读不写**
- AI 系统使用独立只读数据库账号 `ai_reader`
- 所有新建对象在现有 `skillcloud_v2` 库内
- monorepo 结构：`backend/` + `frontend/`（本阶段只建设 backend/）

### 1.2 技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | FastAPI 0.115+, Python 3.12 |
| ORM | SQLAlchemy 2.0 (async) |
| 缓存 | Redis 7 (aioredis) |
| 迁移 | Alembic 1.13+ |
| 任务调度 | APScheduler (AsyncIOScheduler) |
| 数据库 | MySQL 8.0 (只读账号) |

---

## 2. 分层架构

```
Layer 4: 综合分析宽表（物化表，定时刷新）
  v_learner_comprehensive  v_exam_analysis  v_skill_error_summary

Layer 3: 基准统计表（物化表，每月1日4:00刷新）
  dept_benchmark_stats     org_benchmark_stats

Layer 2: 预聚合统计表（已存在，不修改）
  org_daily_stats  org_monthly_stats  org_course_stats  courseware_study_stats

Layer 1: 权限过滤视图（MySQL VIEW，实时）
  v_learner_overview  v_course_overview
```

---

## 3. Layer 1 — 权限过滤视图

### 3.1 `v_learner_overview`（学员学习全景视图）

- **用途**: 为工具层提供统一的学员级查询入口
- **来源表**: `user_info` + `department` + `student_class` + `class_group` + `position` + `user_profile`
- **权限**: VIEW 本身不带用户过滤；权限由 Python 层 `QueryExecutor._inject_permission_where()` 在 Phase 4 实现。Phase 1 仅创建 VIEW 结构

### 3.2 `v_course_overview`（课程全景视图）

- **用途**: 统一的课程+课件查询入口
- **来源表**: `course` + `course_category` + `department` + `course_courseware`
- **包含**: 子查询计算每门课程关联的课件数量

### 3.3 VIEW 安全

- AI 系统账号为只读，无写权限
- 黑名单校验在 SchemaIndexService 层（`validate_query_tables`）

---

## 4. Layer 3 — 基准统计表

### 4.1 `dept_benchmark_stats`（院系基准统计）

每行 = 一个院系在一个统计周期内的聚合指标。

**核心字段**: `avg_completion_rate`, `avg_exam_pass_rate`, `avg_composite_score`, `avg_study_minutes`, `avg_skill_error_rate`, `avg_engagement_score`  
**分位数**: `p25/p50/p75_completion_rate`, `p25/p50/p75_composite_score`  
**唯一键**: `(dept_code, stat_period, stat_date)`

### 4.2 `org_benchmark_stats`（机构基准统计）

结构与 `dept_benchmark_stats` 一致，粒度为 `org_code`。

**唯一键**: `(org_code, stat_period, stat_date)`

### 4.3 刷新策略

- **频率**: 每月 1 日 04:00（Asia/Shanghai）
- **策略**: `DELETE` 目标月份旧数据 + `INSERT` 新聚合
- **兜底**: 每天 03:00 检查是否需要执行
- **数据来源**: `course_grade` + `learning_progress` + `org_daily_stats`

---

## 5. Layer 4 — 综合分析宽表

### 5.1 `v_learner_comprehensive`（学员综合成绩宽表）

| 维度 | 来源 |
|---|---|
| 基础信息 | `user_info`, `department`, `class_group` |
| 进度 | `learning_progress`（按 user 聚合） |
| 成绩 | `course_grade`（按 user 聚合） |
| 考试 | `exam_enrollment`（按 user 聚合） |
| 学习行为 | `study_session_log`（按 user 聚合 SUM） |
| 风险标记 | 计算字段：`is_at_risk`, `risk_type`, `days_since_last_study` |

**刷新**: 每小时整点，增量合并（`ON DUPLICATE KEY UPDATE`）

### 5.2 `v_exam_analysis`（考试分析宽表）

拍平 考场→报名→答题→题目 四级链路。

**包含**: 各题型得分 JSON、答题耗时、正确率/总题数。  
**唯一键**: `(exam_session_code, user_code, attempt_number)`  
**刷新**: 每小时 15 分，增量追加+更新

### 5.3 `v_skill_error_summary`（技能点错误汇总）

从 `skill_error_log` 按 `(courseware_code, step_index, stat_date)` 聚合。

**唯一键**: `(courseware_code, step_index, stat_date)`  
**刷新**: 每天 03:00，`INSERT IGNORE` 追加

### 5.4 刷新任务总览

| 任务 | Cron | 策略 |
|---|---|---|
| `refresh_benchmark_stats` | `0 4 1 * *` | 全量重建上月 |
| `refresh_learner_comprehensive` | `0 * * * *` | 增量 UPSERT |
| `refresh_exam_analysis` | `15 * * * *` | 增量 UPSERT |
| `refresh_skill_error_summary` | `0 3 * * *` | 按天追加 |
| `check_benchmark` | `0 3 * * *` | 兜底检查 |

---

## 6. Python 后端骨架

### 6.1 目录结构

```
backend/
├── app/
│   ├── main.py                    # FastAPI 入口 + 健康检查
│   ├── api/v1/
│   │   └── __init__.py
│   ├── services/ai/
│   │   └── schema_index.py        # SchemaIndexService
│   ├── models/                    # SQLAlchemy ORM（只读映射）
│   │   ├── base.py
│   │   ├── org.py
│   │   ├── user.py
│   │   ├── course.py
│   │   ├── learning.py
│   │   ├── exam.py
│   │   ├── stats.py               # 已存在的预聚合表
│   │   └── benchmark.py           # 新宽表+基准表
│   ├── schemas/
│   │   └── health.py
│   ├── core/
│   │   ├── config.py              # pydantic-settings
│   │   ├── database.py            # async engine + 只读 session
│   │   └── redis.py               # aioredis 连接池
│   └── jobs/
│       ├── scheduler.py           # APScheduler 配置
│       └── refresh_wide_tables.py # 刷新逻辑
├── alembic/
│   └── versions/                  # 7 个迁移文件
├── pyproject.toml
├── requirements.txt
└── tests/
    └── services/ai/
        └── test_schema_index.py
```

### 6.2 SchemaIndexService

完全按 PRD v2.1 §4 实现，四个核心方法：

| 方法 | 注入点 | 场景 |
|---|---|---|
| `get_module_index_text()` | 注入点1 | 意图识别 prompt（~400 tokens） |
| `get_modules_for_intent(intent)` | 注入点2 | 代码路由（0 tokens） |
| `get_table_summaries_text(modules, compact)` | 注入点3 | ReAct prompt（~800 tokens） |
| `validate_query_tables(sql)` | 注入点4 | SQL 黑名单校验（0 tokens） |

**缓存**: Redis `schema_index_v1`（24h TTL）+ 内存一级缓存  
**刷新**: YAML 更新后调用 `refresh()`，删除 Redis key 后重新加载

### 6.3 依赖

- `fastapi>=0.115.0`, `uvicorn[standard]>=0.30.0`
- `sqlalchemy[asyncio]>=2.0.30`, `aiomysql>=0.2.0`
- `redis[hiredis]>=5.0.0`
- `pyyaml>=6.0`, `pydantic>=2.0`, `pydantic-settings>=2.0`
- `apscheduler>=3.10.0`, `alembic>=1.13.0`
- 测试: `pytest>=8.0`, `pytest-asyncio>=0.23`, `httpx>=0.27.0`

### 6.4 ORM 模型策略

- 已存在业务表 → 只读映射，`checkfirst=True`
- 新宽表/基准表 → Alembic migration 创建
- 视图 → Alembic migration 创建（`op.execute("CREATE VIEW ...")`）
- Laravel 框架表 → **不映射**

---

## 7. Alembic 迁移顺序

| 编号 | 内容 | 回滚风险 |
|---|---|---|
| 001 | `dept_benchmark_stats` + `org_benchmark_stats` | 无（新建） |
| 002 | `v_learner_comprehensive` | 无（新建） |
| 003 | `v_exam_analysis` | 无（新建） |
| 004 | `v_skill_error_summary` | 无（新建） |
| 005 | `v_learner_overview` (VIEW) | 无（可 DROP VIEW） |
| 006 | `v_course_overview` (VIEW) | 无 |
| 007 | `qa_session_log` | 无（新建） |

---

## 8. 验收标准

| # | 检查项 | 验证方式 |
|---|---|---|
| 1 | 7 个迁移成功 | `alembic upgrade head` 无报错 |
| 2 | 已有预聚合表未被修改 | 迁移前后 `CHECKSUM TABLE` 一致 |
| 3 | AI 账号只读 | `DELETE/INSERT` 到宽表返回权限拒绝 |
| 4 | SchemaIndexService 正确 | 单元测试：11 模块存在、22 意图路由命中、10 黑名单表拦截 |
| 5 | APScheduler 任务注册 | `scheduler.get_jobs()` 返回 5 个任务 |
| 6 | Redis 缓存 | `GET schema_index_v1` 返回非空 JSON |
| 7 | 健康检查 | `GET /api/v1/health` → 200 |

---

## 9. 不纳入 Phase 1

- QueryExecutor、ToolRegistry、ReAct 引擎 → Phase 4
- IntentClassifier → Phase 3
- SSE 端点 → Phase 5
- 前端任何代码 → Phase 6
- 进化任务 → Phase 7
- 生产部署 → Phase 8
