"""Configuration & environment variables.

All secrets (database URL, JWT secret, Supabase keys) are read from the
environment / .env file. Never hardcode real credentials here.

Local dev defaults are non-secret and safe:
  - SQLite database (no credentials needed)
  - A clearly-fake dev JWT secret (override SECRET_KEY in .env for anything real)

Copy .env.example -> .env and fill in real values for production.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Database ───────────────────────────────────────────────────────────────
    # Local dev default is SQLite (no credentials). In production set e.g.
    # DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname
    DATABASE_URL: str = "sqlite:///./phase2_demo.db"

    # ── Supabase (optional) ────────────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SECRET_KEY: str = ""
    SUPABASE_JWKS_URL: str = ""

    # ── LLM ────────────────────────────────────────────────────────────────────
    # External LLM API (e.g. Groq) — read from env when present
    USE_EXTERNAL_LLM: bool = False
    GROQ_API_KEY: str = ""
    # Use the local model (AIML/negotiation_ai, use_local_hf=True) instead of
    # the fast rule-based mediator. Defaults to a small instruct model that is
    # fast on CPU; set LOCAL_MODEL_ID=bharatgenai/LegalParam for the original
    # 11GB legal model (needs ~11GB RAM and transformers<5).
    USE_LOCAL_MODEL: bool = False
    # HuggingFace model id loaded when USE_LOCAL_MODEL=true.
    LOCAL_MODEL_ID: str = "Qwen/Qwen2.5-3B-Instruct"
    # int8-dynamic-quantize the model on CPU (≈2-3x faster, ~60% less memory).
    # Only applied to standard models on CPU; ignored on CUDA (fp16) and for
    # models with custom remote code (e.g. bharatgenai/LegalParam).
    LOCAL_MODEL_QUANTIZE: bool = True

    # ── Auth ───────────────────────────────────────────────────────────────────
    # WARNING: the default below is a fake dev-only value. Set SECRET_KEY in
    # .env to a long random string in production (e.g. `python -c "import secrets; print(secrets.token_hex(32))"`).
    SECRET_KEY: str = "dev-only-insecure-secret-do-not-use-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # ── File uploads ───────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 20


settings = Settings()
