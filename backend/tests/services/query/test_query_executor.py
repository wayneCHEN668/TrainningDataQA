"""Unit tests for QueryExecutor (mock DB)."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import select, table, column
from app.schemas.auth import UserContext
from app.services.query.query_executor import QueryExecutor


@pytest.fixture
def admin_ctx():
    return UserContext(user_id="u1", user_code="admin1", user_name="Admin", role_level=1, dept_code="D1")


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_schema_svc():
    svc = MagicMock()
    svc.validate_query_tables = MagicMock(return_value=(True, "OK"))
    return svc


class TestQueryExecutor:
    @pytest.mark.asyncio
    async def test_blacklist_rejected(self, admin_ctx, mock_db, mock_schema_svc):
        mock_schema_svc.validate_query_tables = MagicMock(
            return_value=(False, "Query contains forbidden system tables: ['users']")
        )
        executor = QueryExecutor(db=mock_db, user_ctx=admin_ctx, schema_svc=mock_schema_svc)
        t = table("users", column("id"), column("org_code"))
        stmt = select(t)
        with pytest.raises(PermissionError, match="users"):
            await executor.execute(stmt)

    @pytest.mark.asyncio
    async def test_blacklist_allowed(self, admin_ctx, mock_db, mock_schema_svc):
        executor = QueryExecutor(db=mock_db, user_ctx=admin_ctx, schema_svc=mock_schema_svc)
        t = table("user_info", column("id"), column("org_code"))
        stmt = select(t)
        # mock_db.execute is an AsyncMock; return a sync MagicMock as the result
        # so that after await, .mappings() is a real method on a sync object
        result_mock = MagicMock()
        result_mock.mappings.return_value = []
        mock_db.execute.return_value = result_mock
        result = await executor.execute(stmt)
        assert result == []
