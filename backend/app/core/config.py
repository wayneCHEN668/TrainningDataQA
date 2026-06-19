from pathlib import Path
from pydantic import model_validator
from pydantic_settings import BaseSettings

# Resolve .env relative to this file so it works regardless of CWD.
# config.py is at backend/app/core/config.py → 3 parents up to backend/ → 1 more to project root.
_ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"


class Settings(BaseSettings):
    SECRET_KEY: str = "change-me-in-production-use-env-var"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USERNAME: str = "ai_reader"
    DB_PASSWORD: str = ""
    DB_DATABASE: str = "skillcloud_v2"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    REDIS_URL: str = "redis://localhost:6379/0"
    SCHEMA_YAML_PATH: str = "../doc/db_table_index.yaml"

    # Excel report storage
    REPORT_DIR: str = "./data/reports"
    REPORT_TTL_HOURS: int = 24

    # ---- LLM 位置选择 ----
    # "local"  → 使用 LLM_* 字段（本地 Ollama / 任何 OpenAI 兼容 API）
    # "remote" → 使用 DASHSCOPE_* 字段（DashScope / 任何 OpenAI 兼容 API）
    LLM_LOCATION: str = "local"

    # ---- local 模式（LLM_* 字段）----
    LLM_BASE_URL: str = "http://localhost:8000/v1"
    LLM_API_KEY: str = "not-needed"
    LLM_LIGHT_MODEL: str = "qwen2.5-7b-instruct"    # 意图识别（Phase 3）
    LLM_HEAVY_MODEL: str = "qwen2.5-72b-instruct"   # ReAct 推理（Phase 5）

    # ---- remote 模式（DASHSCOPE_* 字段）----
    # 虽然以 DASHSCOPE 命名，但可指向任意兼容 OpenAI 的 API
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_MODEL: str = "qwen3.6-max-preview"

    @model_validator(mode="after")
    def _apply_llm_location(self):
        """当 LLM_LOCATION=remote 时，用 DASHSCOPE_* 覆写 LLM_* 字段。"""
        if self.LLM_LOCATION == "remote":
            self.LLM_BASE_URL = self.DASHSCOPE_BASE_URL
            self.LLM_API_KEY = self.DASHSCOPE_API_KEY
            self.LLM_LIGHT_MODEL = self.DASHSCOPE_MODEL
            self.LLM_HEAVY_MODEL = self.DASHSCOPE_MODEL
        # local → 保持 LLM_* 原始值不变（来自 .env 或默认值）
        return self

    model_config = {
        "env_file": str(_ENV_PATH),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
