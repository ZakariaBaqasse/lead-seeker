from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    MISTRAL_API_KEY: str
    API_SECRET_KEY: str
    GNEWS_API_KEY: str = ""
    SERPAPI_API_KEY: str = ""
    PIPELINE_SCHEDULE_HOUR: int = 6
    PIPELINE_SCHEDULE_MINUTE: int = 0
    TAVILY_API_KEY: str = ""
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
