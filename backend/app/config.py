from functools import lru_cache
from typing import Annotated, Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _parse_cors_origins(value: Any) -> list[str]:
    """Parse the CORS_ORIGINS setting from a string or sequence.

    Pydantic-settings treats ``list[str]`` as JSON by default, which is
    awkward for a comma-separated env var like the one Render sets::

        CORS_ORIGINS=https://app.vercel.app,https://www.example.com

    Accept both forms: a real list (programmatic / .env with JSON), and a
    comma- or whitespace-separated string (the common production shape).
    Empty strings are dropped so an unset variable yields ``[]``.
    """
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        # Try strict JSON first (so ["https://a","https://b"] still works),
        # then fall back to a comma-separated split.
        import json

        stripped = value.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return [str(v).strip() for v in parsed if str(v).strip()]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in stripped.split(",") if item.strip()]
    return [str(value)]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    PROJECT_NAME: str = "Agent Company Simulator"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/agent_company"

    CORS_ORIGINS: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    LOG_LEVEL: str = "INFO"

    # --- LLM configuration (never hardcoded) ---
    LLM_PROVIDER: str = "noop"  # noop | mock | anthropic | openai | gemini | ollama
    LLM_MODEL: str = ""
    LLM_API_KEY: str = ""
    LLM_MAX_TOKENS: int = 1024
    LLM_TEMPERATURE: float = 0.0
    LLM_TIMEOUT: int = 30  # seconds
    LLM_MAX_RETRIES: int = 2
    # Base URL for a locally running Ollama server (used only when
    # LLM_PROVIDER=ollama). Never points at a production/remote host.
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _coerce_cors_origins(cls, value: Any) -> list[str]:
        return _parse_cors_origins(value)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
