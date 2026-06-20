import json
import re
from pathlib import Path

import yaml
import redis.asyncio as aioredis


class SchemaIndexService:
    """db_table_index.yaml three-layer on-demand loading service.

    Four core methods corresponding to four injection points:
    1. get_module_index_text()        -> Injection point 1: Intent classification prompt (~400 tokens)
    2. get_modules_for_intent(intent) -> Injection point 2: Code routing (0 tokens)
    3. get_table_summaries_text()     -> Injection point 3: ReAct prompt (~800 tokens)
    4. validate_query_tables(sql)     -> Injection point 4: SQL blacklist validation (0 tokens)
    """

    CACHE_KEY = "schema_index_v1"

    def __init__(self, yaml_path: str = "../doc/db_table_index.yaml",
                 redis: aioredis.Redis | None = None):
        self._path = Path(yaml_path)
        self._redis = redis
        self._index: dict | None = None

    # -- Called at startup -----------------------------------------

    async def load(self) -> None:
        """Called at startup: parse YAML and cache to Redis."""
        if self._redis:
            cached = await self._redis.get(self.CACHE_KEY)
            if cached:
                self._index = json.loads(cached)
                return

        with open(self._path, encoding="utf-8") as f:
            self._index = yaml.safe_load(f)

        if self._redis:
            await self._redis.set(
                self.CACHE_KEY,
                json.dumps(self._index, ensure_ascii=False),
                ex=86400,  # 24 hours
            )

    async def refresh(self) -> None:
        """Call after deploying updated YAML."""
        if self._redis:
            await self._redis.delete(self.CACHE_KEY)
        self._index = None
        await self.load()

    # -- Injection point 1: Intent classification prompt -----------

    def get_module_index_text(self) -> str:
        module_index = self._index["MODULE_INDEX"]
        lines = ["## Available Data Modules"]
        for name, info in module_index.items():
            answers = info.get("answers", "")
            lines.append(f"- {name}: {answers}")
        return "\n".join(lines)

    # -- Injection point 2: Intent -> Module routing ---------------

    def get_modules_for_intent(self, intent: str) -> list[str]:
        routing = self._index.get("INTENT_MODULE_ROUTING", {})
        return routing.get(intent, ["M10_CompletionGrades", "M9_Statistics"])

    # -- Injection point 3: ReAct prompt (module-filtered) ---------

    def get_table_summaries_text(
        self, modules: list[str], compact: bool = False
    ) -> str:
        summaries = self._index["TABLE_SUMMARIES"]
        lines = ["## Available Data Tables (only query these)"]
        for table_key, info in summaries.items():
            if info.get("module") not in modules:
                continue
            if compact:
                lines.append(
                    f"- {table_key} ({info.get('label', '')}): "
                    f"{info.get('row_meaning', '')}"
                )
            else:
                lines.append("")
                lines.append(f"### {table_key} ({info.get('label', '')})")
                lines.append(f"Row meaning: {info.get('row_meaning', '')}")

                answers = info.get("answers")
                if answers:
                    a = answers if isinstance(answers, str) else " | ".join(answers)
                    lines.append(f"Use for: {a}")

                key_fields = info.get("key_fields")
                if key_fields:
                    f_str = ", ".join(
                        f"{k} ({v})" for k, v in key_fields.items()
                    )
                    lines.append(f"Key fields: {f_str}")

                null_meaning = info.get("null_meaning") or {}
                for field, meaning in null_meaning.items():
                    lines.append(f"Note: {field} = NULL means {meaning}")

                caution = info.get("caution")
                if caution:
                    lines.append(f"Warning: {caution.strip()}")
        return "\n".join(lines)

    # -- Injection point 4: SQL blacklist validation ----------------

    # 旧实现：对编译后 SQL 字符串做正则匹配（QueryExecutor 不再使用，
    # 保留以兼容可能存在的其他调用方/测试代码）。
    FORBIDDEN_TABLE_PATTERN = re.compile(
        r"\b(cache|cache_locks|failed_jobs|job_batches|jobs|"
        r"migrations|password_reset_tokens|personal_access_tokens|"
        r"sessions|users)\b",
        re.IGNORECASE,
    )

    # 新实现：QueryExecutor._validate_tables() 使用的表名集合，
    # 与上面正则中的词表保持一致，供静态分析（直接比对表名集合，无需编译 SQL）使用。
    FORBIDDEN_TABLES = {
        "cache", "cache_locks", "failed_jobs", "job_batches", "jobs",
        "migrations", "password_reset_tokens", "personal_access_tokens",
        "sessions", "users",
    }

    def validate_query_tables(self, sql: str) -> tuple[bool, str]:
        """Validate that SQL does not access forbidden system tables.

        Deprecated path: kept for backward compatibility. QueryExecutor now
        uses the static table-name-set comparison instead (faster, and not
        susceptible to false positives from literal parameter values).
        """
        found = self.FORBIDDEN_TABLE_PATTERN.findall(sql)
        if found:
            unique_found = list(set(found))
            return False, f"Query contains forbidden system tables: {unique_found}"
        return True, "OK"
