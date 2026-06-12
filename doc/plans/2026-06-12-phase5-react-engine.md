# Phase 5 ReAct 引擎 + SSE 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) to implement this plan task-by-task.

**Goal:** 实现 ReAct 推理引擎（封装 LangChain AgentExecutor）和 SSE 流式问答端点，串联 Phase 1-4 的所有组件为完整的 AI 问答流程。

**Architecture:** ReactEngine 包装 LangChain AgentExecutor，通过 astream_events v2 捕获每步事件，转为 8 种 SSE 事件类型。会话管理用 Redis 存近 3 轮历史。

**Tech Stack:** LangChain 0.3+ (AgentExecutor + create_react_agent), FastAPI StreamingResponse, aioredis, ChatOpenAI (streaming)

---

### Task 1: ReactEngine 核心

**Files:**
- Create: `backend/app/services/ai/react_engine.py`

- [ ] **Step 1: Write react_engine.py**

Key class: `ReactEngine`

```python
"""ReAct reasoning engine wrapping LangChain AgentExecutor with SSE event streaming."""
import asyncio
import logging
import time
from typing import AsyncGenerator
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.schemas.auth import UserContext
from app.schemas.sse_events import SSEEvent

logger = logging.getLogger(__name__)

MAX_STEPS = 8
MAX_LLM_RETRIES = 2

REACT_SYSTEM_TEMPLATE = """You are the intelligent analysis engine for the SkillCloudHS training data analysis system.
Answer user questions about training data through Thought -> Action -> Observation cycles.

## Current User
Name: {user_name}
Role: level={role_level}, dept={dept_code}
Current time: {current_time}

## Recent Conversation
{chat_history}

## User Question
{input}

## Intent Classification Result
{intent_info}

## Available Data Tables (only query these)
{schema_context}

## Available Tools
{tools}

## ReAct Format (strictly follow)
Thought: [analyze what you know, what's missing, what to do next]
Action: [tool name]
Action Input: [JSON parameters]
Observation: [tool result]
... (repeat, max 8 steps)
Thought: [confirm you have enough information]
Final Answer: [natural language answer for the user, with data evidence and recommendations]

## Constraints
1. ONLY query tables listed in "Available Data Tables" above
2. ALL numbers must come from tool results -- never invent data
3. When user mentions a course/exam name, call search_course_or_exam FIRST to resolve the code
4. Mark important numbers with **number** format
5. Declare only ONE Action at a time"""


class ReactEngine:
    """Wraps LangChain AgentExecutor for SSE-streamed ReAct reasoning."""

    def __init__(
        self,
        llm_base_url: str,
        llm_model: str,
        schema_context: str,
        user_ctx: UserContext,
        tools: list,
        chat_history: list[dict] | None = None,
    ):
        self._llm = ChatOpenAI(
            model=llm_model,
            base_url=llm_base_url,
            api_key="not-needed",
            temperature=0.2,
            streaming=True,
        )
        self._tools = tools
        self._schema_context = schema_context
        self._user_ctx = user_ctx
        self._history = chat_history or []

    async def run(self, question: str, intent_result) -> AsyncGenerator[SSEEvent, None]:
        history_text = self._format_history()
        intent_text = f"intent={intent_result.intent}, complexity={intent_result.complexity}"

        prompt = ChatPromptTemplate.from_messages([
            ("system", REACT_SYSTEM_TEMPLATE),
            ("human", "{input}"),
        ]).partial(
            user_name=self._user_ctx.user_name,
            role_level=self._user_ctx.role_level,
            dept_code=self._user_ctx.dept_code or "N/A",
            current_time=time.strftime("%Y-%m-%d %H:%M"),
            chat_history=history_text,
            schema_context=self._schema_context,
            tools=self._format_tools(),
            intent_info=intent_text,
        )

        agent = create_react_agent(self._llm, self._tools, prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=self._tools,
            max_iterations=MAX_STEPS,
            return_intermediate_steps=True,
            verbose=False,
        )

        retries = 0
        while retries <= MAX_LLM_RETRIES:
            try:
                step_no = 0
                async for chunk in executor.astream_events(
                    {"input": question}, version="v2"
                ):
                    event_type = chunk.get("event", "")
                    if event_type == "on_tool_start":
                        step_no += 1
                        yield SSEEvent(
                            type="step_start",
                            data={
                                "step_no": step_no,
                                "thought": chunk["data"].get("input", {}).get("__thought__", ""),
                                "action": chunk["name"],
                                "params_summary": _summarize_params(chunk["data"]["input"]),
                            },
                        )
                    elif event_type == "on_tool_end":
                        yield SSEEvent(
                            type="step_done",
                            data={
                                "step_no": step_no,
                                "tool_name": chunk["name"],
                                "result_summary": _summarize_result(
                                    chunk["data"].get("output", "")
                                ),
                            },
                        )
                    elif event_type == "on_chat_model_stream":
                        delta = chunk["data"]["chunk"].content
                        if delta:
                            yield SSEEvent(type="answer_chunk", data={"text_delta": delta})
                return  # Success

            except Exception as e:
                retries += 1
                if retries > MAX_LLM_RETRIES or not _is_retryable(e):
                    yield SSEEvent(type="error", data={
                        "code": "LLM_CALL_FAILED",
                        "message": str(e),
                        "recoverable": False,
                    })
                    return
                await asyncio.sleep(2 ** retries)

    def _format_history(self) -> str:
        if not self._history:
            return "(no previous conversation)"
        lines = []
        for h in self._history:
            role = "User" if h["role"] == "user" else "AI"
            lines.append(f"{role}: {h['content']}")
        return "\n".join(lines)

    def _format_tools(self) -> str:
        lines = []
        for t in self._tools:
            lines.append(f"- {t.name}: {t.description}")
        return "\n".join(lines)


def _summarize_params(params: dict) -> str:
    """Brief summary of tool parameters for SSE display."""
    parts = []
    for k, v in params.items():
        if k.startswith("_"):
            continue
        if isinstance(v, list) and len(v) > 3:
            v = v[:3]
        s = str(v)
        if len(s) > 40:
            s = s[:37] + "..."
        parts.append(f"{k}={s}")
    return ", ".join(parts) if parts else ""


def _summarize_result(result) -> str:
    """Brief summary of tool result for SSE display."""
    if isinstance(result, dict):
        # Pick key metrics to show
        keys = ["completion_rate", "pass_rate", "count", "total",
                "avg_score", "anomalies", "level", "matches", "error_rate"]
        parts = []
        for k in keys:
            if k in result:
                v = result[k]
                if isinstance(v, (int, float)):
                    parts.append(f"{k}={v}")
                elif isinstance(v, list):
                    parts.append(f"{k}=[{len(v)} items]")
        if parts:
            return ", ".join(parts[:4])
        return f"Result with {len(result)} fields"
    s = str(result)
    return s[:120] + "..." if len(s) > 120 else s


def _is_retryable(exc: Exception) -> bool:
    name = type(exc).__name__
    return any(kw in name for kw in ("Timeout", "Connection", "RateLimit"))
```

- [ ] **Step 2: Verify import**

```bash
cd backend && python -c "
from app.services.ai.react_engine import ReactEngine
print('ReactEngine import OK')
"
```

- [ ] **Step 3: Commit**

---

### Task 2: SSE 事件模型 + 格式化工具

**Files:**
- Create: `backend/app/schemas/sse_events.py`

- [ ] **Step 1: Write sse_events.py**

```python
"""SSE event models and formatting."""
import json
from pydantic import BaseModel


class SSEEvent(BaseModel):
    type: str
    data: dict


def format_sse(event_type: str, data: dict) -> str:
    """Format a dict as an SSE event string."""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {payload}\n\n"
```

- [ ] **Step 2: Commit**

---

### Task 3: 会话管理器

**Files:**
- Create: `backend/app/services/ai/session_manager.py`

- [ ] **Step 1: Write session_manager.py**

```python
"""Session history management via Redis + qa_session_log recording."""
import json
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

CHAT_HISTORY_TTL = 86400  # 24 hours
MAX_HISTORY_ENTRIES = 6   # 3 rounds of Q&A


async def load_chat_history(
    redis: aioredis.Redis | None,
    session_id: str | None,
    user_id: str,
) -> list[dict]:
    if not redis or not session_id:
        return []
    key = f"chat_history:{user_id}:{session_id}"
    raw = await redis.get(key)
    return json.loads(raw) if raw else []


async def save_chat_history(
    redis: aioredis.Redis | None,
    session_id: str | None,
    user_id: str,
    question: str,
    answer_summary: str,
) -> None:
    if not redis or not session_id:
        return
    key = f"chat_history:{user_id}:{session_id}"
    history = await load_chat_history(redis, session_id, user_id)
    history.append({"role": "user", "content": question})
    history.append({"role": "ai", "content": answer_summary})
    history = history[-MAX_HISTORY_ENTRIES:]
    await redis.set(key, json.dumps(history, ensure_ascii=False), ex=CHAT_HISTORY_TTL)


async def log_qa_session(
    db: AsyncSession,
    session_id: str,
    user_id: str,
    org_code: str,
    question: str,
    intent: str | None,
    complexity: str | None,
    modules_used: list[str],
    tools_used: list[str],
    steps_count: int,
    duration_ms: int,
    total_tokens: int,
) -> None:
    try:
        await db.execute(text("""
            INSERT INTO qa_session_log
                (session_id, user_id, org_code, question, intent, complexity,
                 modules_used, steps_count, tools_used, duration_ms, total_tokens)
            VALUES
                (:sid, :uid, :org, :q, :intent, :comp,
                 :mods, :steps, :tools, :dur, :tokens)
        """), {
            "sid": session_id, "uid": user_id, "org": org_code,
            "q": question, "intent": intent, "comp": complexity,
            "mods": json.dumps(modules_used), "steps": steps_count,
            "tools": json.dumps(tools_used), "dur": duration_ms,
            "tokens": total_tokens,
        })
        await db.commit()
    except Exception:
        logger.exception("Failed to log qa_session")
```

- [ ] **Step 2: Commit**

---

### Task 4: SSE 问答端点

**Files:**
- Create: `backend/app/api/v1/ai_query.py`
- Modify: `backend/app/main.py` (register router)

- [ ] **Step 1: Write ai_query.py**

```python
"""SSE streaming endpoint for AI query."""
import asyncio
import json
import time
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.config import settings
from app.api.deps import get_current_user
from app.schemas.auth import UserContext
from app.schemas.sse_events import SSEEvent, format_sse
from app.services.ai.schema_index import SchemaIndexService
from app.services.ai.intent_classifier import IntentClassifier, ClassificationError
from app.services.ai.react_engine import ReactEngine
from app.services.ai.session_manager import (
    load_chat_history, save_chat_history, log_qa_session,
)
from app.services.query.tool_registry import ToolRegistry

router = APIRouter(prefix="/api/v1", tags=["ai-query"])


@router.get("/ai-query")
async def ai_query(
    q: str = Query(..., min_length=1, description="User question"),
    session_id: str | None = Query(default=None),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> StreamingResponse:

    async def event_stream():
        start = time.monotonic()
        modules_used = []
        tools_used = []
        total_steps = 0

        # [1] Load chat history
        history = await load_chat_history(redis, session_id, current_user.user_id)

        # [2] Intent classification
        schema_svc = SchemaIndexService(redis=redis)
        await schema_svc.load()
        classifier = IntentClassifier(schema_svc=schema_svc)

        try:
            intent_result = await classifier.classify(q, current_user)
            yield format_sse("intent_resolved", {
                "intent": intent_result.intent,
                "complexity": intent_result.complexity,
                "confidence": intent_result.confidence,
            })
        except ClassificationError:
            options = classifier.get_clarification_options(q, current_user)
            yield format_sse("clarification_options", {
                "options": [o.model_dump() for o in options],
            })
            return

        # [3] Schema context by intent modules
        modules = schema_svc.get_modules_for_intent(intent_result.intent)
        modules_used = modules
        schema_context = schema_svc.get_table_summaries_text(
            modules=modules,
            compact=(intent_result.complexity == "simple"),
        )

        # [4] Tools
        registry = ToolRegistry(db=db, user_ctx=current_user, schema_svc=schema_svc)
        tools = registry.get_all_tools()

        # [5] ReAct engine
        engine = ReactEngine(
            llm_base_url=settings.LLM_BASE_URL,
            llm_model=settings.LLM_HEAVY_MODEL,
            schema_context=schema_context,
            user_ctx=current_user,
            tools=tools,
            chat_history=history,
        )

        steps_data = []
        async for event in engine.run(q, intent_result):
            yield format_sse(event.type, event.data)
            if event.type in ("step_start", "step_done"):
                ...
            if event.type == "step_done":
                total_steps = event.data.get("step_no", total_steps)
                tools_used.append(event.data.get("tool_name", ""))
                steps_data.append(event.data)

        # [6] Done
        duration_ms = int((time.monotonic() - start) * 1000)
        yield format_sse("evidence", {"steps": steps_data})
        yield format_sse("done", {
            "total_steps": total_steps,
            "duration_ms": duration_ms,
        })

        # [7] Background: save history + log
        answer_summary = steps_data[-1].get("result_summary", "") if steps_data else ""
        asyncio.create_task(save_chat_history(
            redis, session_id, current_user.user_id, q, answer_summary,
        ))
        asyncio.create_task(log_qa_session(
            db, session_id or "", current_user.user_id,
            current_user.dept_code or "", q,
            intent_result.intent, intent_result.complexity,
            modules_used, tools_used, total_steps, duration_ms, 0,
        ))

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 2: Register router in main.py**

Add to `backend/app/main.py`:
```python
from app.api.v1.ai_query import router as ai_query_router
app.include_router(ai_query_router)
```

- [ ] **Step 3: Verify imports**

```bash
cd backend && python -c "
from app.api.v1.ai_query import router
print('ai_query router import OK')
"
```

- [ ] **Step 4: Commit**

---

### Task 5: 单元测试

**Files:**
- Create: `backend/tests/services/ai/test_react_engine.py`
- Create: `backend/tests/services/ai/test_session_manager.py`

- [ ] **Step 1: Write test_react_engine.py** (6 tests: SSE format, prompt template checks, engine event flow with mocked LLM)

- [ ] **Step 2: Write test_session_manager.py** (4 tests: empty history, save/load, cap at 6, no redis fallback)

- [ ] **Step 3: Run tests** -> 10+ pass

- [ ] **Step 4: Commit**

---

### Task 6: 集成验证

- [ ] **Step 1: Run full test suite**

```bash
cd backend && python -m pytest tests/ -v
```

- [ ] **Step 2: Verify all imports**

```bash
cd backend && python -c "
from app.api.v1.ai_query import router
from app.services.ai.react_engine import ReactEngine
from app.services.ai.session_manager import load_chat_history, save_chat_history
from app.schemas.sse_events import SSEEvent, format_sse
print('All Phase 5 imports OK')
"
```

- [ ] **Step 3: Verify SSE format**

```python
result = format_sse("test", {"key": "value"})
assert result == 'event: test\ndata: {"key": "value"}\n\n'
```

- [ ] **Step 4: Commit**

---

## Task Dependencies

```
Task 2 (SSE models) ─> independent
Task 1 (ReactEngine) ─> depends on Task 2
Task 3 (SessionManager) ─> independent
Task 4 (SSE endpoint) ─> depends on Task 1, 2, 3
Task 5 (Tests) ─> depends on all above
Task 6 (Verification) ─> depends on Task 5
```

## Time Estimate

| Task | Time |
|------|------|
| 1: ReactEngine core | 30 min |
| 2: SSE models | 5 min |
| 3: Session manager | 15 min |
| 4: SSE endpoint | 20 min |
| 5: Unit tests | 20 min |
| 6: Verification | 10 min |
| **Total** | **~1.75 hours** |
