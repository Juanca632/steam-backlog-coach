"""Application settings, loaded from environment variables / .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    steam_api_key: str = ""
    steam_id: str = ""
    database_url: str = "sqlite:///../data/backlog.db"

    llm_provider: str = "anthropic"
    llm_api_key: str = ""
    llm_model: str = "claude-sonnet-5"


settings = Settings()
