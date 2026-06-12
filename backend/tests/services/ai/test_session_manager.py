"""Unit tests for session manager (mock Redis)."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.ai.session_manager import (
    load_chat_history, save_chat_history,
    CHAT_HISTORY_TTL, MAX_HISTORY_ENTRIES,
)


class TestLoadChatHistory:
    @pytest.mark.asyncio
    async def test_no_redis_returns_empty(self):
        result = await load_chat_history(None, "s1", "u1")
        assert result == []

    @pytest.mark.asyncio
    async def test_no_session_id_returns_empty(self):
        redis = AsyncMock()
        result = await load_chat_history(redis, None, "u1")
        assert result == []

    @pytest.mark.asyncio
    async def test_loads_existing_history(self):
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=json.dumps([
            {"role": "user", "content": "hello"},
        ]))
        result = await load_chat_history(redis, "s1", "u1")
        assert len(result) == 1
        assert result[0]["role"] == "user"


class TestSaveChatHistory:
    @pytest.mark.asyncio
    async def test_no_redis_skips(self):
        await save_chat_history(None, "s1", "u1", "q", "a")
        # Should not raise

    @pytest.mark.asyncio
    async def test_no_session_id_skips(self):
        redis = AsyncMock()
        await save_chat_history(redis, None, "u1", "q", "a")
        redis.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_caps_at_max_entries(self):
        redis = AsyncMock()
        existing = [{"role": "user", "content": f"msg{i}"} for i in range(10)]
        redis.get = AsyncMock(return_value=json.dumps(existing))
        captured_value = None

        async def mock_set(key, value, ex):
            nonlocal captured_value
            captured_value = value

        redis.set = mock_set
        await save_chat_history(redis, "s1", "u1", "new_q", "new_a")
        saved = json.loads(captured_value)
        assert len(saved) == MAX_HISTORY_ENTRIES  # 6
        assert saved[-2]["content"] == "new_q"
        assert saved[-1]["content"] == "new_a"
