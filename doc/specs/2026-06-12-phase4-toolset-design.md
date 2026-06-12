# Phase 4 — 工具集 设计文档

**项目**: SkillCloudHS AI 数据问答系统
**日期**: 2026-06-12
**状态**: 已确认

---

## 1. 概述

Phase 4 实现 13 个 LangChain StructuredTool + QueryExecutor 权限注入层，为 Phase 5 的 ReAct 推理引擎提供数据查询能力。

### 1.1 核心指标

| 指标 | 要求 |
|------|------|
| 工具注册数 | 13 个（8 查询型 + 3 计算型 + 2 辅助型） |
| 权限注入 | 4 种角色硬约束，不可绕过 |
| 黑名单校验 | 10 张禁止表全部拦截 |
| 查询方式 | SQLAlchemy Core select() 表达式语言 |
| 数据源 | 所有工具操作 Phase 1 宽表/视图，不查原始业务表 |

---

## 2. 整体架构

```
ToolRegistry (13 StructuredTools)
  |
  v
QueryExecutor
  |-- SQLAlchemy Core select() 构建查询
  |-- 自动注入权限 WHERE (基于 UserContext)
  |-- 黑名单表名校验 (SchemaIndexService)
  |-- 返回 list[dict]
  |
  v
AsyncSession -> MySQL (v_learner_comprehensive, v_exam_analysis, ...)
```

### 2.1 产出文件

```
backend/app/services/query/
  __init__.py
  query_executor.py      # QueryExecutor
  permission_scope.py    # PermissionScope
  tool_registry.py       # 13 个 LangChain StructuredTool

backend/app/schemas/
  tools.py               # 每个工具的 Pydantic Input 模型
```

---

## 3. PermissionScope

从 UserContext 计算权限过滤条件：

| role_level | 注入条件 |
|-----------|---------|
| 0 超管 | 不注入任何 WHERE |
| 1 管理员 | WHERE org_code = ? |
| 2 教师 | WHERE dept_code = ? |
| 3 学生 | WHERE user_id = ? |

QueryExecutor 取首个在被查询表中存在的权限列来注入。如果表中没有任何权限列（如字典表），允许查询。

---

## 4. QueryExecutor

三个职责：
1. 自动注入权限 WHERE 条件（硬约束）
2. 黑名单表名校验（硬约束，通过 SchemaIndexService.validate_query_tables）
3. 执行 SQLAlchemy Core select() → 返回 list[dict]

所有查询型工具通过 QueryExecutor 执行，权限由闭包隐式注入，LLM 无法传入越权参数。

---

## 5. 13 个工具

### 查询型 (Q1-Q8) — 查宽表/视图

| 工具 | 数据源 | 输入 |
|------|--------|------|
| query_completion_rate | v_learner_comprehensive | scope_type, time_start, time_end, course_code?, group_by |
| query_incomplete_learners | v_learner_comprehensive | scope_type, course_code, urgency_threshold_days |
| query_exam_performance | v_exam_analysis | scope_type, exam_session_code?, time range, group_by |
| query_skill_error_analysis | v_skill_error_summary | courseware_code, top_n |
| query_learning_trend | org_daily_stats / org_monthly_stats | scope_type, metric, time range, granularity |
| query_at_risk_learners | v_learner_comprehensive (is_at_risk=1) | scope_type, risk_types |
| query_individual_profile | learner_profile + course_grade | user_code |
| query_org_overview | org_daily_stats + course_grade | time_start, time_end |

### 计算型 (C1-C3) — Python 内存计算

| 工具 | 职责 |
|------|------|
| compute_period_comparison | 环比/同比计算 |
| detect_anomalies | 时间序列异常检测 |
| evaluate_metric_level | 指标水平评估 (vs 基准) |

### 辅助型 (A1-A2) — 字典/基准查询

| 工具 | 数据源 |
|------|--------|
| get_benchmark | dept_benchmark_stats / org_benchmark_stats |
| search_course_or_exam | course / exam_session (LIKE 模糊匹配) |

### 工具定义模式

每个工具 = `StructuredTool.from_function(coroutine=async_func, name=..., description=..., args_schema=PydanticModel)`

---

## 6. 工具描述（给 LLM 看的关键信息）

| 工具 | description (英文，给 LLM) |
|------|--------------------------|
| query_completion_rate | Query learning completion rate. Use for: completion percentage, which depts/classes have low completion. group_by can be dept/class/course. |
| query_incomplete_learners | Find learners who haven't completed a course. Returns list with urgency level. |
| query_exam_performance | Query exam pass rate, avg score, score distribution. Use for: exam results, pass/fail analysis, which exam was hardest. |
| query_skill_error_analysis | Find steps with highest error rates in an OC courseware. Returns top N error-prone steps. |
| query_learning_trend | Get trend data over time (daily/weekly/monthly). Metrics: study_minutes/completions/exam_pass/active_users. |
| query_at_risk_learners | Identify at-risk learners by type: inactive (no study >7d), low_score (composite<60), near_deadline. |
| query_individual_profile | Get a single learner's complete profile: courses, weak areas, study patterns, engagement score. |
| query_org_overview | Get organizational overview: total learners, avg completion, best/worst performers, key highlights. |
| compute_period_comparison | Compare two periods (current vs previous). Returns delta and percentage change. |
| detect_anomalies | Detect statistical anomalies in time series data using sigma threshold. |
| evaluate_metric_level | Evaluate a metric value against benchmarks: excellent/good/average/below/poor. |
| get_benchmark | Get dept or org benchmark statistics (avg, percentiles) for comparison. |
| search_course_or_exam | Fuzzy search course or exam by name. Returns matching codes for use in other tools. |

---

## 7. 16 个 Pydantic Input 模型

详见实施计划中的完整代码。关键原则：每个 Input 只包含 LLM 可传入的业务参数，权限参数（user_id, dept_code, org_code）由 QueryExecutor 闭包注入，不出现在 args_schema 中。

---

## 8. 测试策略

### 单元测试（16+ 个，Mock DB）

- PermissionScope: 4 个角色过滤条件测试
- QueryExecutor: 权限注入逻辑 + 黑名单校验
- 计算型工具: 3 个纯函数测试
- ToolRegistry: 13 工具注册 + schema 验证
- Pydantic: Input 序列化/校验

### 集成测试（4 个，需 DB）

- 真实查询完成率/考试数据
- 管理员 vs 学生权限范围验证
- 课程名称模糊搜索

### 验收标准

| 指标 | 要求 |
|------|------|
| 工具注册数 | 13 个 |
| 权限注入 | 4 种角色覆盖 |
| 黑名单 | 10 张表拦截 |
| 单元测试 | 16+ 通过 |
| LangChain 兼容 | Phase 5 可直接接入 create_react_agent |

---

## 9. 不纳入 Phase 4

- ReAct 推理引擎 → Phase 5
- SSE 问答端点 → Phase 5
- 3 个 Pure-LLM 工具 (generate_recommendation, generate_chart_spec, query_compliance_status) → Phase 5
- 前端 → Phase 6
