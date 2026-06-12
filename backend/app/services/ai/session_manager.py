"""Session history management via Redis + qa_session_log recording."""
import json
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

CHAT_HISTORY_TTL = 86400  # 24 hours
MAX_HISTORY_ENTRIES = 6   # 3 rounds of Q&A per session


async def load_chat_history(
    redis: aioredis.Redis | None,
    session_id: str | None,
    user_id: str,
) -> list[dict]:
    """Load recent chat history from Redis. Returns empty list if no session or no Redis."""
    if not redis or not session_id:
        return []
    key = f"chat_history:{user_id}:{session_id}"
    try:
        raw = await redis.get(key)
        return json.loads(raw) if raw else []
    except Exception:
        logger.exception("Failed to load chat history")
        return []


async def save_chat_history(
    redis: aioredis.Redis | None,
    session_id: str | None,
    user_id: str,
    question: str,
    answer_summary: str,
) -> None:
    """Append Q&A to Redis chat history. Caps at MAX_HISTORY_ENTRIES."""
    if not redis or not session_id:
        return
    try:
        key = f"chat_history:{user_id}:{session_id}"
        history = await load_chat_history(redis, session_id, user_id)
        history.append({"role": "user", "content": question})
        history.append({"role": "ai", "content": answer_summary})
        history = history[-MAX_HISTORY_ENTRIES:]
        await redis.set(
            key,
            json.dumps(history, ensure_ascii=False),
            ex=CHAT_HISTORY_TTL,
        )
    except Exception:
        logger.exception("Failed to save chat history")


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
                "mods": json.dumps(modules_used),
                "steps": steps_count,
                "tools": json.dumps(tools_used),
                "dur": duration_ms,
                "tokens": total_tokens,
            },
        )
        await db.commit()
    except Exception:
        logger.exception("Failed to log qa_session")
