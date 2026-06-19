"""Unit tests for session manager (mock DB)."""
import pytest
from unittest.mock import AsyncMock
from app.services.ai.session_manager import log_qa_session


class TestLogQaSession:
    @pytest.mark.asyncio
    async def test_logs_session(self):
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        await log_qa_session(
            db, "sid1", "uid1", "dept1", "how are you?",
            "grade_query", "simple",
            ["grades"], ["get_grade"], 2, 5000, 0,
        )
        db.execute.assert_called_once()
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_exception_is_silent(self):
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=Exception("DB down"))
        # Should not raise
        await log_qa_session(
            db, "sid1", "uid1", "dept1", "q",
            None, None, [], [], 0, 0, 0,
        )
