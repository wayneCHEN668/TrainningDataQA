# Phase 7 — 自我进化机制 设计文档

**项目**: SkillCloudHS AI 数据问答系统
**日期**: 2026-06-12
**状态**: 已确认

---

## 1. 概述

Phase 7 实现系统的自我进化机制——每日自动分析 QA 日志和未匹配问题，生成改进报告供管理员审查。不做自动模板修改。

### 1.1 核心指标

| 指标 | 要求 |
|------|------|
| 分析周期 | 过去 7 天滚动 |
| 报告生成 | 每日 02:00 |
| 报告位置 | doc/analysis/YYYY-MM-DD-evolution-report.md |
| Redis 缓存 | evolution_stats:daily, 7 天 TTL |

---

## 2. 架构

```
每日 02:00 APScheduler evolution_job
  |
  +-- qa_session_log (最近7天) --> 意图分布 + 低质量识别 + 整体指标
  +-- doc/unmatched_queries.md --> 解析表格 + 高频模式检测
  |
  +-- EvolutionAnalyzer.analyze(days=7)
  |
  +-- 生成: doc/analysis/YYYY-MM-DD-evolution-report.md
  +-- 缓存: Redis evolution_stats:daily
  +-- 提供: GET /api/v1/admin/stats (role_level <= 1)
```

---

## 3. 产出的 4 个文件/端点

### 3.1 `backend/app/services/ai/evolution_analyzer.py`
- EvolutionAnalyzer: analyze(days), _query_overall_metrics, _query_intent_distribution
- _query_low_quality: 四个条件（negative_feedback, fallback_used, too_many_steps, too_slow）
- _parse_unmatched_queries: 解析 markdown 表格 → 统计数量 + 高频模式
- EvolutionReport: to_markdown(), to_summary_json()

### 3.2 `backend/app/jobs/evolution_job.py`
- `run_daily_evolution()`: 每日 02:00, 生成报告 + Redis 缓存

### 3.3 `backend/app/api/v1/admin.py`
- `GET /api/v1/admin/stats`: 从 Redis 读 evolution_stats:daily, 仅管理员可访问

### 3.4 每日报告格式
```
doc/analysis/YYYY-MM-DD-evolution-report.md
  S1 整体指标（7 日趋势）
  S2 意图分布（Top10 + 低质量率）
  S3 未匹配问题摘要（新增/累计/高频模式）
  S4 改进建议（模板优化/未匹配/数据层）
```

---

## 4. 测试策略

### 单元测试（9+）
- _parse_unmatched_queries (3): 正常表格/空文件/格式异常
- 低质量判定 (4): 四个条件各自触发
- 报告格式化 (2): to_markdown/to_summary_json

### 集成测试（2）
- 插入测试数据 → analyzer 验证报告
- Admin API 权限验证

### 验收标准

| 指标 | 要求 |
|------|------|
| 单元测试 | 9+ 通过 |
| 每日报告 | doc/analysis/ 下自动生成 |
| Redis 缓存 | 7 天 TTL |
| Admin API | role>1 被拒绝 |
