from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/news_dashboard"

    # AI – LLM (Ollama)
    llm_model: str = "llama3.1:8b"

    # AI – Embeddings (local sentence-transformers)
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"

    # Dedup
    dedup_similarity_threshold: float = 0.92
    dedup_window_hours: int = 24

    # Telegram
    telegram_api_id: int | None = None
    telegram_api_hash: str | None = None
    telegram_session_name: str = "news_dashboard"

    # Ingestion
    initial_backfill_hours: int = 24
    polling_enabled: bool = True
    polling_interval_seconds: int = 60

    # Media storage
    media_storage_path: str = "media"
    media_max_file_size_mb: int = 50
    media_download_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
