from __future__ import annotations
from typing import Optional, List, Dict, Any
"""全局配置 — 环境变量驱动"""
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # 应用信息
    APP_NAME: str = "GTCS 全球贸易通关系统"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:8008", "http://localhost:5173", "http://localhost:80"]

    # 数据库 (SQLite for dev, PG for prod)
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'gtcs.db'}"

    # JWT — 生产环境必须通过 SECRET_KEY 环境变量覆盖
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    @property
    def effective_secret_key(self) -> str:
        sk = self.SECRET_KEY
        if sk == "change-me-in-production":
            import warnings
            warnings.warn("SECRET_KEY 使用默认值，请通过 .env 文件设置 SECRET_KEY")
        return sk

    # 数据源
    DATA_SOURCE: str = "db"  # db / mock / hybrid

    class Config:
        env_file = ".env"


settings = Settings()
