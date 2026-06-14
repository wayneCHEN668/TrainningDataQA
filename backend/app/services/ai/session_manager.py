"""Session analytics: qa_session_log recording.

Chat history is now stored client-side (localStorage) and sent with each request.
Server-side storage of conversation context is no longer needed.
"""
import json
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


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
    """Record qa_session_log entry. Fire-and-forget, never raise."""
    try:
        await db.execute(
            text("""
                INSERT INTO qa_session_log
                    (session_id, user_id, org_code, question, intent, complexity,
                     modules_used, steps_count, tools_used, duration_ms, total_tokens)
                VALUES
                    (:sid, :uid, :org, :q, :intent, :comp,
                     :mods, :steps, :tools, :dur, :tokens)
            """),
            {
                "sid": session_id,
                "uid": user_id,
                "org": org_code,
                "q": question,
                "intent": intent,
                "comp": complexity,
                "mods": json.dumps(modules_used, ensure_ascii=False),
                "steps": steps_count,
                "tools": json.dumps(tools_used, ensure_ascii=False),
                "dur": duration_ms,
                "tokens": total_tokens,
            },
        )
        await db.commit()
    except Exception:
        logger.exception("Failed to log qa_session")
