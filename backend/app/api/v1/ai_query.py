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
from app.schemas.sse_events import format_sse
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
        registry = ToolRegistry(
            db=db, user_ctx=current_user, schema_svc=schema_svc
        )
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
            if event.type == "step_done":
                total_steps = event.data.get("step_no", total_steps)
                tools_used.append(event.data.get("tool_name", ""))
                steps_data.append(event.data)

        # [6] Final events
        duration_ms = int((time.monotonic() - start) * 1000)
        yield format_sse("evidence", {"steps": steps_data})
        yield format_sse("done", {
            "total_steps": total_steps,
            "duration_ms": duration_ms,
        })

        # [7] Background: save history + log (fire-and-forget)
        answer_summary = (
            steps_data[-1].get("result_summary", "") if steps_data else ""
        )
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
