"""Query execution layer with automatic permission injection and blacklist validation."""
from sqlalchemy import Select
from sqlalchemy.sql import column as get_column
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import UserContext
from app.services.query.permission_scope import PermissionScope
from app.services.ai.schema_index import SchemaIndexService


class QueryExecutor:
    """Unified query execution layer for all tool functions.

    Three responsibilities:
    1. Auto-inject permission WHERE clause (hard constraint)
    2. Blacklist table name validation (hard constraint)
    3. Execute SQLAlchemy Core select() -> return list[dict]
    """

    def __init__(
        self,
        db: AsyncSession,
        user_ctx: UserContext,
        schema_svc: SchemaIndexService,
    ):
        self._db = db
        self._scope = PermissionScope(user_ctx)
        self._schema = schema_svc

    async def execute(self, stmt: Select) -> list[dict]:
        """Execute query with automatic permission injection + blacklist validation."""
        stmt = self._inject_permission(stmt)
        self._validate_tables(stmt)
        result = await self._db.execute(stmt)
        return [dict(row) for row in result.mappings()]

    def _inject_permission(self, stmt: Select) -> Select:
        """Auto-inject permission WHERE clause.

        Picks the first permission column (org_code/dept_code/user_id)
        that exists in the queried table. If none match, allows the query
        (e.g., for dictionary tables like courseware_type).
        """
        if self._scope.is_superadmin:
            return stmt
        from_clause = stmt.get_final_froms()[0]
        available_columns = {c.name for c in from_clause.columns}
        for col_name, value in self._scope.get_filters():
            if col_name in available_columns:
                if isinstance(value, list):
                    return stmt.where(get_column(col_name).in_(value))
                return stmt.where(get_column(col_name) == value)
        return stmt

    def _validate_tables(self, stmt: Select) -> None:
        """Blacklist validation: reject queries touching forbidden tables."""
        compiled = stmt.compile(compile_kwargs={"literal_binds": True})
        ok, msg = self._schema.validate_query_tables(str(compiled))
        if not ok:
            raise PermissionError(msg)
