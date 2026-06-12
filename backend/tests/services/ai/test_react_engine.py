"""Unit tests for ReactEngine (mock LLM, no real DB)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.schemas.auth import UserContext
from app.schemas.sse_events import SSEEvent, format_sse
from app.services.ai.react_engine import (
    _summarize_params, _summarize_result, _is_retryable,
)


@pytest.fixture
def user_ctx():
    return UserContext(user_id="u1", user_code="admin1", user_name="Admin", role_level=1, dept_code="D1")


class TestSSEFormatting:
    def test_format_sse(self):
        result = format_sse("test_event", {"key": "value"})
        assert result.startswith("event: test_event\n")
        assert 'data: {"key": "value"}' in result
        assert result.endswith("\n\n")

    def test_format_sse_chinese(self):
        result = format_sse("done", {"message": "分析完成", "steps": 3})
        assert "分析完成" in result


class TestSummarizeHelpers:
    def test_summarize_params_normal(self):
        result = _summarize_params({
            "scope_type": "all",
            "time_start": "2026-01-01",
            "course_code": None,
        })
        assert "scope_type=all" in result
        assert "time_start=2026-01-01" in result

    def test_summarize_params_filters_underscore(self):
        result = _summarize_params({"__thought__": "skip", "user_code": "s1"})
        assert "__thought__" not in result
        assert "user_code=s1" in result

    def test_summarize_result_dict(self):
        result = _summarize_result({
            "completion_rate": 85.5,
            "count": 320,
            "unused_field": "should not appear",
        })
        assert "completion_rate=85.5" in result
        assert "count=320" in result

    def test_summarize_result_str(self):
        result = _summarize_result("A simple string result")
        assert "A simple string result" in result


class TestRetryable:
    def test_timeout_is_retryable(self):
        class FakeTimeout(Exception):
            pass
        assert _is_retryable(FakeTimeout("Timeout"))

    def test_value_error_not_retryable(self):
        assert not _is_retryable(ValueError("bad input"))

    def test_connection_is_retryable(self):
        class ConnectionError(Exception):
            pass
        assert _is_retryable(ConnectionError("conn refused"))
