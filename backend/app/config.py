from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    PROJECT_NAME: str = "Agent Company Simulator"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/agent_company"

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # --- LLM configuration (never hardcoded) ---
    LLM_PROVIDER: str = "noop"  # noop | mock | anthropic | openai
    LLM_MODEL: str = ""
    LLM_API_KEY: str = ""
    LLM_MAX_TOKENS: int = 1024
    LLM_TEMPERATURE: float = 0.0
    LLM_TIMEOUT: int = 30  # seconds


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
