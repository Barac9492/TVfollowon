from __future__ import annotations

from typing import List
from pydantic_settings import BaseSettings
from pathlib import Path

_BASE = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "Follow-on Screener"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = f"sqlite:///{_BASE / 'data' / 'screener.db'}"

    # File uploads
    UPLOAD_DIR: str = str(_BASE / "data" / "uploads")

    # Slack (optional)
    SLACK_BOT_TOKEN: str = ""

    # Claude API (optional)
    CLAUDE_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Currency
    KRW_TO_USD_RATE: float = 1350.0  # 1 USD = 1350 KRW

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
