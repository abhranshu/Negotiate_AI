"""
Configuration & environment variables.
Copy .env.example to .env and fill in your values.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database — defaults to SQLite (no install needed to get started)
    DATABASE_URL: str = "sqlite:///./negotiateai.db"

    # LLM — set your Anthropic key for Module 4 & 5 (optional; falls back to keyword heuristics)
    ANTHROPIC_API_KEY: str = ""

    # Auth
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # File uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 20

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
