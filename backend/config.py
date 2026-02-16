from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # LLM (Cerebras — Llama 3.3 70B)
    CEREBRAS_API_KEY: str = ""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./researchpilot.db"

    # Storage
    UPLOAD_DIR: str = "./uploads"
    CHROMA_DIR: str = "./chroma_data"
    MAX_FILE_SIZE_MB: int = 50

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # App
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
