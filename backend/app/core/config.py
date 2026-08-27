from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Docsnary API"
    app_env: str = "development"
    app_version: str = "0.1.0"

    database_url: str
    redis_url: str

    ai_provider: str = "mock"
    ai_api_key: str = ""
    ai_model: str = "mock-model"
    ai_timeout: float = 30.0
    ai_max_retries: int = 3

    embedding_provider: str = "mock"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 32

    storage_root: str = "storage"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()