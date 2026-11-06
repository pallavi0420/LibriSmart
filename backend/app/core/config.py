import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator


_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEFAULT_DB_PATH = os.path.join(_BASE_DIR, "librismart.db").replace("\\", "/")


class Settings(BaseSettings):
    APP_NAME: str = "LibriSmart API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "librismart_super_secret_development_key_2026_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{_DEFAULT_DB_PATH}"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["*"]

    # Library Circulation & Seating Defaults
    DEFAULT_MAX_BORROW_LIMIT: int = 3
    DEFAULT_LOAN_DURATION_DAYS: int = 14
    DEFAULT_FINE_PER_DAY_CENTS: int = 50
    DEFAULT_GRACE_PERIOD_MINUTES: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
