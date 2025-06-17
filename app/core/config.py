import os


class Settings:
    SECRET_KEY: str = "a_very_secret_key_that_should_be_long_and_random"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = "sqlite:///./app.db"
    TEST_DATABASE_URL: str = "sqlite:///./test.db"
    ALGORITHM: str = "HS256"


settings = Settings()
