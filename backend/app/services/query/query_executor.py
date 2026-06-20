"""Query execution layer with automatic permission injection and blacklist validation."""
from sqlalchemy import Select
from sqlalchemy.sql import column as get_column
from sqlalchemy.sql.selectable import Join, Alias, Subquery
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import UserContext
from app.services.query.permission_scope import PermissionScope
from app.services.ai.schema_index import SchemaIndexService


def _extract_table_names(from_obj) -> set[str]:
    """递归提取一个 FromClause 涉及的所有真实表名（不含别名/JOIN 包装）。

    处理三种情况：
    - Join：递归拆解 .left / .right，两边各自可能还是 Join/Alias/Table
    - Alias：取底层真实表名（from_obj.element），而不是别名字符串本身
    - Subquery：递归进子查询内部的 froms（兜底，当前工具层未实际使用子查询）
    - 普通 Table：直接取 .name
    """
    names: set[str] = set()
    if isinstance(from_obj, Join):
        names |= _extract_table_names(from_obj.left)
        names |= _extract_table_names(from_obj.right)
    elif isinstance(from_obj, Alias):
        names |= _extract_table_names(from_obj.element)
    elif isinstance(from_obj, Subquery):
        inner_stmt = from_obj.element
        if hasattr(inner_stmt, "get_final_froms"):
            for f in inner_stmt.get_final_froms():
                names |= _extract_table_names(f)
    elif hasattr(from_obj, "name") and from_obj.name:
        names.add(from_obj.name)
    return names


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
        """Blacklist validation: reject queries touching forbidden tables.

        性能优化：原实现用 stmt.compile(compile_kwargs={"literal_binds": True})
        把整个 Select 编译成完整 SQL 字符串（参数内联），再用正则在字符串上做
        黑名单匹配。literal_binds=True 比普通 compile 慢，且每次工具调用都要
        重新执行一遍，一次问答可能调用 2-5 个工具，是个可以轻松省掉的固定成本。

        现在改为静态分析：直接从 stmt.get_final_froms() 递归提取本次查询
        实际涉及的表名集合，与黑名单直接做集合比对，完全不需要编译 SQL。

        附带收益：原来的字符串正则匹配是对“整段编译后 SQL”做扫描，因为用了
        literal_binds=True，查询参数的字面量值也被内联进了 SQL 字符串——如果
        某次查询参数恰好包含 "sessions" 这类词（比如用户姓名/课程名里恰好有
        这个词），会被误判为命中黑名单表名而拒绝查询。改成只比对真实表名集合后，
        这种误伤完全消失，校验也变得更精确。
        """
        table_names: set[str] = set()
        for from_obj in stmt.get_final_froms():
            table_names |= _extract_table_names(from_obj)

        forbidden_hit = table_names & self._schema.FORBIDDEN_TABLES
        if forbidden_hit:
            raise PermissionError(
                f"Query contains forbidden system tables: {sorted(forbidden_hit)}"
            )
