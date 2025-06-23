from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "a_very_secret_key_that_should_be_in_a_file"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Use aiosqlite for async support
    DATABASE_URL: str = "sqlite+aiosqlite:///./sql_app.db"

    UPLOADS_DIR: str = "uploads"
    AVATARS_DIR: str = os.path.join(UPLOADS_DIR, "avatars")
    TEST_DATABASE_URL: str = "sqlite:///./test.db"
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()
