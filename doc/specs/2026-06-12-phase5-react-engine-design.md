# Phase 5 — ReAct 引擎 + SSE 流式输出 设计文档

**项目**: SkillCloudHS AI 数据问答系统
**日期**: 2026-06-12
**状态**: 已确认

---

## 1. 概述

Phase 5 是系统的核心——串联 InteentClassifier + ToolRegistry + SchemaIndexService 成完整的 ReAct 推理流程，通过 SSE (Server-Sent Events) 流式推送给前端。

### 1.1 核心指标

| 指标 | 要求 |
|------|------|
| ReAct 最大步数 | <= 8 步 |
| LLM 重试 | 最多 2 次，指数退避 (2s, 4s) |
| 会话历史 | 最多 6 条（3 轮），Redis 24h TTL |
| SSE 事件类型 | 8 种 |
| Simple 问题响应 | < 20s |
| Complex 问题响应 | < 35s |

---

## 2. 整体架构

```
POST /api/v1/ai-query?q=...&session_id=xxx
  |
  v
[1] JWT Auth -> UserContext
[2] Redis 加载会话历史 (近3轮)
[3] IntentClassifier.classify() -> IntentResult | clarification_options
[4] SchemaIndexService 按模块加载表摘要
[5] ToolRegistry(db, user_ctx, schema_svc) -> 13 StructuredTools
[6] ReactEngine.run() -> LangChain AgentExecutor.astream_events()
[7] Redis 更新会话历史 (后台异步)
[8] qa_session_log 记录 (后台异步)
  |
  v
SSE StreamingResponse -> 8 种事件类型
```

### 2.1 产出文件

```
backend/app/services/ai/
  react_engine.py       # ReactEngine: 封装 LangChain AgentExecutor
  session_manager.py    # 会话历史 Redis 读写 + qa_session_log

backend/app/api/v1/
  ai_query.py           # GET /api/v1/ai-query SSE 端点

backend/app/schemas/
  sse_events.py         # SSE 事件 Pydantic 模型
```

---

## 3. ReactEngine

### 3.1 初始化

```python
engine = ReactEngine(
    llm_base_url=settings.LLM_BASE_URL,
    llm_model=settings.LLM_HEAVY_MODEL,    # 72B 重量模型
    schema_context=schema_context,          # SchemaIndexService 输出的表摘要
    user_ctx=current_user,
    tools=tools,                            # 13 StructuredTools
    chat_history=history,                   # 近 3 轮对话
)
```

### 3.2 ReAct System Prompt

由四部分拼接：角色声明 + 运行时上下文（用户/权限/时间/模块索引）+ 近期对话 + ReAct 格式定义 + 约束条件。

### 3.3 LangChain 事件 → SSE 映射

| LangChain Event | SSE Event |
|----------------|-----------|
| (手动) | intent_resolved |
| on_tool_start | step_start |
| on_tool_end | step_done |
| on_chat_model_stream | answer_chunk |
| (手动) | evidence |
| (手动) | done |
| (异常) | error |

### 3.4 关键约束
- 所有数字必须来自工具返回，不编造
- 课程名/考试名 → 先调 search_course_or_exam 解析
- 重要数字用 **数字** 标记
- 每次只声明一个 Action

---

## 4. SSE 端点 + 会话管理

### 4.1 GET /api/v1/ai-query

- 参数: `q` (问题), `session_id` (可选)
- 认证: Bearer Token (JWT)
- 响应: `text/event-stream`
- 头: `Cache-Control: no-cache`, `X-Accel-Buffering: no`

### 4.2 8 种 SSE 事件

| 事件 | 触发时机 | Payload 关键字段 |
|------|---------|-----------------|
| intent_resolved | 意图识别完成 | intent, complexity, confidence |
| clarification_options | LLM 不可用降级 | options[{index, text, intent}] |
| step_start | ReAct 步骤开始 | step_no, thought, action, params_summary |
| step_done | ReAct 步骤完成 | step_no, tool_name, result_summary |
| answer_chunk | LLM 流式输出 | text_delta |
| evidence | 所有步骤完成 | steps[{step_no, tool, key_finding}] |
| done | 全部完成 | total_steps, total_tokens, duration_ms |
| error | 任何错误 | code, message, recoverable |

### 4.3 会话历史

- Redis key: `chat_history:{user_id}:{session_id}`
- 值: JSON list, 最多 6 条 (3轮 Q&A)
- TTL: 24 小时
- 无 session_id → 不存历史

### 4.4 qa_session_log 异步写入

- 不阻塞 SSE 流
- 记录: session_id, user_id, org_code, question, intent, complexity, modules_used, steps_count, tools_used, duration_ms, total_tokens, asked_at

---

## 5. 错误处理

### 5.1 错误码

| Code | 含义 | Recoverable |
|------|------|-------------|
| INTENT_CLASSIFICATION_FAILED | -> clarification_options | yes |
| PERMISSION_ERROR | 越权/黑名单表 | no |
| TOOL_EXECUTION_FAILED | 单工具失败 | yes (换工具) |
| LLM_CALL_FAILED | LLM 不可用 | no (2次重试后) |
| MAX_STEPS_EXCEEDED | >8 步 | partial |
| DB_CONNECTION_ERROR | DB 不可用 | no |
| INTERNAL_ERROR | 未知 | no |

### 5.2 超时策略

| 阶段 | 超时 | 处理 |
|------|------|------|
| 意图识别 | 5s+8s | 走 clarification |
| 单步工具 | 30s | 标记失败 |
| ReAct 整体 | 120s | 输出已有结论 |
| SSE 总时长 | 180s | 关闭连接 |

---

## 6. 测试策略

### 6.1 单元测试（~15 个，无 LLM/DB）

- SSE 格式化 (2): 格式正确、JSON 可序列化
- Prompt 模板 (4): 用户/表摘要/工具/历史注入
- ReactEngine (3): 事件流生成
- 会话管理 (3): load/save/trim
- 错误处理 (3): clarify/重试/超步数

### 6.2 集成测试（~4 个，Mock LLM + 真实 DB）

- 完整流程 SSE 事件序列
- 追问降级流程
- 权限注入在完整流程生效
- 会话历史持久化

### 6.3 验收标准

| 指标 | 要求 |
|------|------|
| 单元测试 | 15+ 通过 |
| SSE 事件类型 | 8 种全部覆盖 |
| ReAct < 8 步 | 是 |
| LLM 重试 < 2 | 是，指数退避 |
| 会话历史 < 6 条 | 是 |

---

## 7. 不纳入 Phase 5

- 前端 React Chat UI → Phase 6
- 进化机制 (每日模板生成) → Phase 7
- 生产部署 → Phase 8
