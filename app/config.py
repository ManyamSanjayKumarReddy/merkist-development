from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "production"

    DATABASE_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    INSTAGRAM_APP_ID: str
    INSTAGRAM_APP_SECRET: str
    INSTAGRAM_REDIRECT_URI: str

    ALLOWED_ORIGINS: List[str] = ["*"]
    FRONTEND_URL: str

    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()