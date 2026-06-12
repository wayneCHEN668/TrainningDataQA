from pydantic_settings import BaseSettings


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
    # LLM 通用配置
    LLM_BASE_URL: str = "http://localhost:8000/v1"
    LLM_API_KEY: str = "not-needed"

    # 意图识别用轻量模型（Phase 3）
    LLM_LIGHT_MODEL: str = "qwen2.5-7b-instruct"

    # ReAct 推理用重量模型（Phase 5 预留）
    LLM_HEAVY_MODEL: str = "qwen2.5-72b-instruct"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
