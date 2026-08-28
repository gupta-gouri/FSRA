from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "FSRA Backend"
    API_PREFIX: str = "/api" 
    ENVIRONMENT: str = "development"

    SUPABASE_URL: str
    SUPABASE_KEY: str

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        case_sensitive = True,
        extra = "ignore"
    )

settings = Settings()
