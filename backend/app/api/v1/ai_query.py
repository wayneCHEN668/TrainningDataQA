"""SSE streaming endpoint for AI query."""
import asyncio
import json
import time
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db, AsyncSessionLocal
from app.core.config import settings
from app.api.deps import get_current_user
from app.schemas.auth import UserContext
from app.schemas.intent import IntentResult
from app.schemas.sse_events import format_sse
from app.services.ai.schema_index import SchemaIndexService
from app.services.ai.intent_classifier import IntentClassifier, ClassificationError
from app.services.ai.react_engine import ReactEngine
from app.services.ai.session_manager import log_qa_session
from app.services.query.tool_registry import ToolRegistry


class AIQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question")
    history: list[dict] = Field(default_factory=list, description="Recent chat history [{role, content}, ...]")
    clarification_intent: str | None = Field(default=None, description="Pre-classified intent when user selected a clarification option — bypasses re-classification")


class FeedbackRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="AI 消息 ID")
    question: str = Field(..., min_length=1, description="用户问题")
    answer: str = Field(default="", description="AI 回答内容")
    feedback_type: str = Field(..., pattern=r"^(like|dislike|wrong)$", description="反馈类型")


router = APIRouter(prefix="/api/v1", tags=["ai-query"])


# ---------------------------------------------------------------------------
# History truncation — prevent LLM context window overflow
# ---------------------------------------------------------------------------

# Reserve space for system prompt (~2000 tokens) + tool results
MAX_HISTORY_TOKENS = 2000
# Maximum conversation turns to retain (1 turn = 2 messages)
MAX_HISTORY_TURNS = 10


def _trim_history(history: list[dict], max_turns: int, max_tokens: int) -> list[dict]:
    """Trim history to recent N turns while respecting token budget.
    
    Strategy:
    1. Keep only the most recent max_turns * 2 messages
    2. Estimate tokens (rough: 1 token ≈ 3 chars for mixed CJK/English)
    3. Drop oldest messages if total exceeds max_tokens
    
    This prevents context window overflow when system prompt + tools + history
    would exceed the LLM's limit.
    """
    if not history:
        return []
    
    # Keep only recent turns (each turn = user + ai = 2 messages)
    recent = history[-(max_turns * 2):]
    
    def estimate_tokens(msg: dict) -> int:
        """Rough token estimate: ~1 token per 3 characters (mixed content)."""
        content = msg.get("content", "")
        return max(1, len(content) // 3)
    
    # Build trimmed list from most recent, stopping at token limit
    total = 0
    trimmed = []
    for msg in reversed(recent):
        msg_tokens = estimate_tokens(msg)
        if total + msg_tokens > max_tokens:
            break
        trimmed.insert(0, msg)
        total += msg_tokens
    
    return trimmed


@router.post("/ai-query")
async def ai_query(
    request: Request,
    body: AIQueryRequest,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:

    q = body.question
    # Trim history to prevent context window overflow
    history = _trim_history(body.history or [], MAX_HISTORY_TURNS, MAX_HISTORY_TOKENS)

    async def event_stream():
        import uuid
        start = time.monotonic()
        session_id = uuid.uuid4().hex[:16]

        try:
            async for chunk in _run_pipeline(
                request, body, current_user, db, q, history,
                session_id, start,
            ):
                yield chunk

        except asyncio.CancelledError:
            # Client disconnected — propagate so the ASGI server can
            # clean up the connection properly; nothing to send.
            raise

        except Exception as exc:
            # Catch-all safety net: any unhandled exception anywhere in the
            # pipeline (intent classification, schema loading, tool registry,
            # ReAct engine, Excel generation, etc.) lands here instead of
            # silently terminating the generator and leaving the client
            # waiting forever with no `done` or `error` event.
            print(f"[Backend SSE] [FATAL] 未捕获异常: {type(exc).__name__}: {exc}", flush=True)
            import traceback
            traceback.print_exc()
            try:
                yield format_sse("error", {
                    "code": "INTERNAL_ERROR",
                    "message": "系统处理请求时发生未知错误，请稍后重试。",
                    "recoverable": True,
                })
                yield format_sse("done", {
                    "total_steps": 0,
                    "duration_ms": int((time.monotonic() - start) * 1000),
                    "session_id": session_id,
                })
            except Exception:
                # Even the error-reporting itself failed (e.g. connection
                # already closed) — nothing more we can do.
                pass

    async def _run_pipeline(
        request, body, current_user, db, q, history, session_id, start,
    ):
        import sys
        modules_used = []
        tools_used = []
        total_steps = 0

        print("[Backend SSE] ===== 开始处理请求 =====", flush=True)
        print(f"[Backend SSE] 问题: {q[:200]}", flush=True)
        print(f"[Backend SSE] 用户: {current_user.user_name} (role={current_user.role_level})", flush=True)
        print(f"[Backend SSE] 聊天历史: {len(history)} 条", flush=True)

        # [2] Clarification loop-breaker: count recent clarification rounds
        # Detection: type field == "clarification" (primary) or content contains clarification markers (fallback)
        CLARIFICATION_CONTENT_MARKERS = ["请选择以下选项以澄清", "clarification", "澄清您的问题"]
        
        def _is_clarification_msg(h: dict) -> bool:
            """Check if a history message is a clarification response."""
            if h.get("role") != "ai":
                return False
            # Primary: check type field (set by frontend when saving clarification rounds)
            if h.get("type") == "clarification":
                return True
            # Fallback: check content for clarification markers (backward compatibility)
            content = h.get("content", "")
            return any(marker in content for marker in CLARIFICATION_CONTENT_MARKERS)
        
        clarification_count = sum(
            1 for h in history[-6:]
            if _is_clarification_msg(h)
        )
        MAX_CLARIFICATION_ROUNDS = 3
        if clarification_count >= MAX_CLARIFICATION_ROUNDS:
            print(f"[Backend SSE] [2] 澄清循环已达上限 ({clarification_count} 轮), 停止", flush=True)
            yield format_sse("error", {
                "code": "CLARIFICATION_LIMIT",
                "message": "连续多次未能理解问题，请尝试用更具体的方式描述需求。",
                "recoverable": True,
            })
            return

        # [3] Intent classification (reuse startup SchemaIndexService singleton)
        print("[Backend SSE] [3] 开始意图分类...", flush=True)
        t3 = time.monotonic()
        schema_svc: SchemaIndexService = request.app.state.schema_svc
        classifier = IntentClassifier(schema_svc=schema_svc)

        # Bypass re-classification when user selected a clarification option
        CLARIFICATION_INTENTS = {
            "查询全部各院系的课件完成率": "COMPLETION_RATE_QUERY",
            "查询全部未完成学习的学员名单": "INCOMPLETE_LEARNER_QUERY",
            "查询全部学习进度的整体概况": "ORG_OVERVIEW_QUERY",
        }

        if body.clarification_intent:
            bypass_intent = body.clarification_intent
            if bypass_intent in CLARIFICATION_INTENTS:
                bypass_intent = CLARIFICATION_INTENTS[bypass_intent]
            print(f"[Backend SSE] [3] 用户选择澄清选项, 意图跳过分类: {bypass_intent}", flush=True)
            intent_result = IntentResult(
                intent=bypass_intent,
                confidence=0.9,
                complexity="simple",
                need_clarification=False,
            )
        else:
            try:
                intent_result = await classifier.classify(q, current_user)
                print(f"[Backend SSE] [3] 意图分类完成, 耗时: {(time.monotonic()-t3)*1000:.0f}ms", flush=True)
                print(f"[Backend SSE] [3] 意图: {intent_result.intent}, 复杂度: {intent_result.complexity}, 置信度: {intent_result.confidence}", flush=True)

                # Check if intent classifier suggests clarification
                if intent_result.need_clarification:
                    clarification_q = getattr(intent_result, "clarification_question", None)
                    print(f"[Backend SSE] [3] 意图分类建议澄清: {clarification_q}", flush=True)
                    classifier.save_unmatched(q, current_user)
                    options = classifier.get_clarification_options(q, current_user)
                    yield format_sse("clarification_options", {
                        "options": [o.model_dump() for o in options],
                        "clarification_question": clarification_q or "",
                    })
                    return

            except ClassificationError:
                print(f"[Backend SSE] [3] 意图分类失败, 返回澄清选项 (耗时: {(time.monotonic()-t3)*1000:.0f}ms)", flush=True)
                classifier.save_unmatched(q, current_user)
                options = classifier.get_clarification_options(q, current_user)
                yield format_sse("clarification_options", {
                    "options": [o.model_dump() for o in options],
                })
                return

        output_mode = getattr(intent_result, "output_mode", "analysis")
        print(f"[Backend SSE] output_mode={output_mode}", flush=True)

        yield format_sse("intent_resolved", {
            "intent": intent_result.intent,
            "complexity": intent_result.complexity,
            "confidence": intent_result.confidence,
        })

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
            schema_svc=schema_svc,
        )

        steps_data = []
        step_idx = 0
        async for event in engine.run(q, intent_result, output_mode=output_mode):
            step_idx += 1
            print(f"[Backend SSE] [5] ReAct 事件 #{step_idx}: type={event.type}, data_keys={list(event.data.keys()) if event.data else 'None'}", flush=True)
            yield format_sse(event.type, event.data)
            if event.type == "step_done":
                total_steps = event.data.get("step_no", total_steps)
                tools_used.append(event.data.get("tool_name", ""))
                steps_data.append(event.data)
        print(f"[Backend SSE] [5] ReAct 引擎完成, 耗时: {(time.monotonic()-t5)*1000:.0f}ms, 总步数: {len(steps_data)}", flush=True)

        # [5b] Excel 报表生成（后处理，不消耗 ReAct 步骤）
        if output_mode == "report":
            tool_results = getattr(engine, "_tool_results", [])
            if tool_results:
                print(f"[Backend SSE] [5b] 生成Excel报表, 工具结果数: {len(tool_results)}", flush=True)
                try:
                    from app.services.export.excel_generator import ExcelGenerator
                    excel_gen = ExcelGenerator()
                    output = await asyncio.to_thread(
                        excel_gen.generate,
                        tool_results, q,
                        current_user.dept_code or "全部机构",
                        settings.REPORT_DIR,
                    )
                    if output:
                        print(f"[Backend SSE] [5b] Excel生成成功: {output['file_name']}", flush=True)
                        yield format_sse("download_ready", {
                            "file_name": output["file_name"],
                            "file_url": output["file_url"],
                            "file_size": output["file_size"],
                            "sheets": output["sheets"],
                            "total_rows": output["total_rows"],
                            "total_columns": output["total_columns"],
                        })
                    else:
                        print(f"[Backend SSE] [5b] 无可导出的表格数据", flush=True)
                except Exception as exc:
                    print(f"[Backend SSE] [5b] Excel生成失败: {exc}", flush=True)
                    yield format_sse("error", {
                        "code": "EXCEL_GENERATION_FAILED",
                        "message": f"报表生成失败: {str(exc)[:100]}",
                        "recoverable": False,
                    })

        # [6] Final events
        duration_ms = int((time.monotonic() - start) * 1000)
        yield format_sse("evidence", {"steps": steps_data})
        yield format_sse("done", {
            "total_steps": total_steps,
            "duration_ms": duration_ms,
            "session_id": session_id,
        })

        # [7] Background: log to qa_session_log (analytics, fire-and-forget)
        async def _safe_log():
            try:
                async with AsyncSessionLocal() as bg_db:
                    await log_qa_session(
                        bg_db, session_id, current_user.user_id,
                        dept_code=current_user.dept_code or "", question=q,
                        intent=intent_result.intent, complexity=intent_result.complexity,
                        modules_used=modules_used, tools_used=tools_used,
                        steps_count=total_steps, duration_ms=duration_ms, total_tokens=0,
                        fallback_used=getattr(engine, "fallback_used", False),
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
