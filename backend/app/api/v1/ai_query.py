"""SSE streaming endpoint for AI query."""
import asyncio
import json
import time
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db, AsyncSessionLocal
from app.core.config import settings
from app.api.deps import get_current_user
from app.schemas.auth import UserContext
from app.schemas.sse_events import format_sse
from app.services.ai.schema_index import SchemaIndexService
from app.services.ai.intent_classifier import IntentClassifier, ClassificationError
from app.services.ai.react_engine import ReactEngine
from app.services.ai.session_manager import log_qa_session
from app.services.query.tool_registry import ToolRegistry


class AIQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question")
    history: list[dict] = Field(default_factory=list, description="Recent chat history [{role, content}, ...]")


class FeedbackRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="AI 消息 ID")
    question: str = Field(..., min_length=1, description="用户问题")
    answer: str = Field(default="", description="AI 回答内容")
    feedback_type: str = Field(..., pattern=r"^(like|dislike|wrong)$", description="反馈类型")


router = APIRouter(prefix="/api/v1", tags=["ai-query"])


@router.post("/ai-query")
async def ai_query(
    body: AIQueryRequest,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:

    q = body.question
    history = body.history

    async def event_stream():
        import sys
        start = time.monotonic()
        modules_used = []
        tools_used = []
        total_steps = 0

        print("[Backend SSE] ===== 开始处理请求 =====", flush=True)
        print(f"[Backend SSE] 问题: {q[:200]}", flush=True)
        print(f"[Backend SSE] 用户: {current_user.user_name} (role={current_user.role_level})", flush=True)
        print(f"[Backend SSE] 聊天历史: {len(history)} 条", flush=True)

        # [2] Intent classification (SchemaIndexService, load from YAML)
        print("[Backend SSE] [2] 开始意图分类...", flush=True)
        t2 = time.monotonic()
        schema_svc = SchemaIndexService()
        await schema_svc.load()
        print(f"[Backend SSE] [2] Schema 从 YAML 文件加载完成", flush=True)
        classifier = IntentClassifier(schema_svc=schema_svc)

        try:
            intent_result = await classifier.classify(q, current_user)
            print(f"[Backend SSE] [2] 意图分类完成, 耗时: {(time.monotonic()-t2)*1000:.0f}ms", flush=True)
            print(f"[Backend SSE] [2] 意图: {intent_result.intent}, 复杂度: {intent_result.complexity}, 置信度: {intent_result.confidence}", flush=True)
            yield format_sse("intent_resolved", {
                "intent": intent_result.intent,
                "complexity": intent_result.complexity,
                "confidence": intent_result.confidence,
            })
        except ClassificationError:
            print(f"[Backend SSE] [2] 意图分类失败, 返回澄清选项 (耗时: {(time.monotonic()-t2)*1000:.0f}ms)", flush=True)
            options = classifier.get_clarification_options(q, current_user)
            yield format_sse("clarification_options", {
                "options": [o.model_dump() for o in options],
            })
            return

        # [3] Schema context by intent modules
        t3 = time.monotonic()
        modules = schema_svc.get_modules_for_intent(intent_result.intent)
        modules_used = modules
        schema_context = schema_svc.get_table_summaries_text(
            modules=modules,
            compact=(intent_result.complexity == "simple"),
        )
        print(f"[Backend SSE] [3] Schema 加载完成, 耗时: {(time.monotonic()-t3)*1000:.0f}ms, 模块数: {len(modules)}", flush=True)

        # [4] Tools
        t4 = time.monotonic()
        registry = ToolRegistry(
            db=db, user_ctx=current_user, schema_svc=schema_svc
        )
        tools = registry.get_all_tools()
        print(f"[Backend SSE] [4] 工具注册完成, 耗时: {(time.monotonic()-t4)*1000:.0f}ms, 工具数: {len(tools)}", flush=True)

        # [5] ReAct engine — history comes from client, no server-side storage needed
        print(f"[Backend SSE] [5] 启动 ReAct 引擎...", flush=True)
        print(f"[Backend SSE] [5] LLM URL: {settings.LLM_BASE_URL}, Model: {settings.LLM_HEAVY_MODEL}", flush=True)
        t5 = time.monotonic()
        engine = ReactEngine(
            llm_base_url=settings.LLM_BASE_URL,
            llm_model=settings.LLM_HEAVY_MODEL,
            schema_context=schema_context,
            user_ctx=current_user,
            tools=tools,
            chat_history=history,
            llm_api_key=settings.LLM_API_KEY,
        )

        steps_data = []
        step_idx = 0
        async for event in engine.run(q, intent_result):
            step_idx += 1
            print(f"[Backend SSE] [5] ReAct 事件 #{step_idx}: type={event.type}, data_keys={list(event.data.keys()) if event.data else 'None'}", flush=True)
            yield format_sse(event.type, event.data)
            if event.type == "step_done":
                total_steps = event.data.get("step_no", total_steps)
                tools_used.append(event.data.get("tool_name", ""))
                steps_data.append(event.data)
        print(f"[Backend SSE] [5] ReAct 引擎完成, 耗时: {(time.monotonic()-t5)*1000:.0f}ms, 总步数: {len(steps_data)}", flush=True)

        # [6] Final events
        duration_ms = int((time.monotonic() - start) * 1000)
        yield format_sse("evidence", {"steps": steps_data})
        yield format_sse("done", {
            "total_steps": total_steps,
            "duration_ms": duration_ms,
        })

        # [7] Background: log to qa_session_log (analytics, fire-and-forget)
        async def _safe_log():
            try:
                async with AsyncSessionLocal() as bg_db:
                    await log_qa_session(
                        bg_db, "", current_user.user_id,
                        current_user.dept_code or "", q,
                        intent_result.intent, intent_result.complexity,
                        modules_used, tools_used, total_steps, duration_ms, 0,
                    )
            except Exception:
                pass
        asyncio.create_task(_safe_log())

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/ai-query/feedback")
async def submit_feedback(
    req: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """Submit user feedback for an AI answer.

    Stores feedback in qa_session_log.user_feedback:
    - like → 1 (有帮助)
    - dislike → -1 (不够好)
    - wrong → -2 (完全错误)
    """
    feedback_map = {"like": 1, "dislike": -1, "wrong": -2}
    feedback_value = feedback_map[req.feedback_type]

    try:
        await db.execute(
            text("""
                UPDATE qa_session_log
                SET user_feedback = :feedback
                WHERE session_id = :sid AND user_id = :uid
            """),
            {
                "feedback": feedback_value,
                "sid": req.session_id,
                "uid": current_user.user_id,
            },
        )
        await db.commit()
    except Exception:
        # Fire-and-forget — don't fail if logging fails
        pass

    return {"status": "ok"}
