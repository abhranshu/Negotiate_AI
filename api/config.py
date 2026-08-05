"""Configuration & environment variables."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase PostgreSQL
    DATABASE_URL: str = "postgresql+psycopg2://postgres:3A7oCDP6ku46otyM@db.vficltziofvdswguubzy.supabase.co:5432/postgres"

    # Supabase URL & Key
    SUPABASE_URL: str = "https://vficltziofvdswguubzy.supabase.co"
    SUPABASE_KEY: str = "sb_publishable_c9oCNc_BioGwjZ3IogNxSg_w_DxTgB1"

    # LLM — no external API key required
    USE_EXTERNAL_LLM: bool = False

    # Auth
    SECRET_KEY: str = "nai2025msme-odr-platform-secret-key-minimum-32-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # File uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 20

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
