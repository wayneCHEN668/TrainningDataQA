"""Unit tests for ToolRegistry."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.schemas.auth import UserContext
from app.services.query.tool_registry import ToolRegistry


@pytest.fixture
def user_ctx():
    return UserContext(user_id="u1", user_code="admin1", user_name="Admin", role_level=1, dept_code="D1")


@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db


@pytest.fixture
def mock_schema_svc():
    svc = MagicMock()
    svc.validate_query_tables = MagicMock(return_value=(True, "OK"))
    svc.get_module_index_text = MagicMock(return_value="## Modules")
    return svc


class TestToolRegistry:
    def test_registers_13_tools(self, mock_db, user_ctx, mock_schema_svc):
        registry = ToolRegistry(db=mock_db, user_ctx=user_ctx, schema_svc=mock_schema_svc)
        tools = registry.get_all_tools()
        assert len(tools) == 13, f"Expected 13 tools, got {len(tools)}"

    def test_tool_names_unique(self, mock_db, user_ctx, mock_schema_svc):
        registry = ToolRegistry(db=mock_db, user_ctx=user_ctx, schema_svc=mock_schema_svc)
        tools = registry.get_all_tools()
        names = [t.name for t in tools]
        assert len(names) == len(set(names)), f"Duplicate names: {names}"

    def test_all_tools_have_args_schema(self, mock_db, user_ctx, mock_schema_svc):
        registry = ToolRegistry(db=mock_db, user_ctx=user_ctx, schema_svc=mock_schema_svc)
        tools = registry.get_all_tools()
        for tool in tools:
            assert tool.args_schema is not None, f"Tool {tool.name} has no args_schema"

    def test_all_tools_have_description(self, mock_db, user_ctx, mock_schema_svc):
        registry = ToolRegistry(db=mock_db, user_ctx=user_ctx, schema_svc=mock_schema_svc)
        tools = registry.get_all_tools()
        for tool in tools:
            assert tool.description, f"Tool {tool.name} has empty description"
