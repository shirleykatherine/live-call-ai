"""
Application configuration — all settings come from environment variables.
Loads the project-level .env file reliably regardless of the working directory.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root:
# Live Call AI/
# ├── .env
# └── backend/
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- LLM ----------------------------------------------------------------
    llm_api_key: str = ""
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "openai/gpt-4o-mini"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024

    # --- Embeddings ---------------------------------------------------------
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- Database -----------------------------------------------------------
    database_url: str = "sqlite:///./live_call_ai.db"

    # --- Vector DB ----------------------------------------------------------
    vector_db_path: str = "./data/chroma_db"
    vector_db_collection: str = "knowledge_base"

    # --- Speech-to-Text -----------------------------------------------------
    # Provider: "browser" | "deepgram" | "assemblyai"
    stt_provider: str = "browser"
    stt_api_key: str = ""

    # --- WebSocket ----------------------------------------------------------
    ws_heartbeat_interval: int = 30

    # --- App ----------------------------------------------------------------
    app_name: str = "Live Call Co-pilot"
    app_version: str = "1.0.0"
    debug: bool = False
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()