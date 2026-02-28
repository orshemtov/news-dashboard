from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/news_dashboard"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"

    # AI – LLM
    llm_provider: Literal["ollama", "openai"] = "ollama"
    llm_model: str = "llama3.1:8b"
    ollama_base_url: str = "http://localhost:11434"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # AI – Embeddings
    embedding_provider: Literal["local", "openai"] = "local"
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dimensions: int = 384
    openai_embedding_model: str = "text-embedding-3-small"

    # Dedup
    dedup_similarity_threshold: float = 0.92
    dedup_window_hours: int = 24

    # Telegram
    telegram_api_id: int | None = None
    telegram_api_hash: str | None = None
    telegram_session_name: str = "news_dashboard"

    # Ingestion
    telegram_poll_interval_seconds: int = 60
    initial_backfill_hours: int = 24
    polling_enabled: bool = True
    polling_interval_seconds: int = 300


@lru_cache
def get_settings() -> Settings:
    return Settings()
