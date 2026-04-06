from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    MISTRAL_API_KEY: str
    API_SECRET_KEY: str
    PIPELINE_SCHEDULE_HOUR: int = 6
    PIPELINE_SCHEDULE_MINUTE: int = 0
    GNEWS_API_KEY: Optional[str] = None


settings = Settings()
