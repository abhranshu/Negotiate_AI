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
    # External LLM API (e.g. Groq) — read from env when present.
    # This project does not depend on Groq for its voice pipeline anymore;
    # leave this empty on the low-resource VM.
    USE_EXTERNAL_LLM: bool = False
    GROQ_API_KEY: str = ""
    # Use a local HF model for negotiation instead of the fast rule-based
    # mediator. Defaults to a small instruct model that is fast on CPU.
    # The low-resource VM deploy uses USE_LOCAL_MODEL=false (rule-based).
    USE_LOCAL_MODEL: bool = False
    # HuggingFace model id loaded when USE_LOCAL_MODEL=true.
    LOCAL_MODEL_ID: str = "Qwen/Qwen2.5-3B-Instruct"
    # int8-dynamic-quantize the model on CPU (~2-3x faster, ~60% less memory).
    # Only applied to standard models on CPU; ignored on CUDA (fp16) and for
    # models with custom remote code (e.g. bharatgenai/LegalParam).
    LOCAL_MODEL_QUANTIZE: bool = True

    # ── Auth ───────────────────────────────────────────────────────────────────
    # WARNING: the default below is a fake dev-only value. Set SECRET_KEY in
    # .env to a long random string in production (e.g. `python -c "import secrets; print(secrets.token_hex(32))"`).
    SECRET_KEY: str = "dev-only-insecure-secret-do-not-use-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    # Database connection pool sizing for this single-VM deploy.
    # 5 is plenty for a single uvicorn worker; raise only with more workers.
    DB_POOL_SIZE: int = 5
    # Uvicorn worker count for this VM.
    # Keep this at 1 on the low-resource box so we do not fork multiple copies
    # of the app/db pool and eat into the 7.6 GB RAM budget.
    UVICORN_WORKERS: int = 1
    # Disable FastAPI/Starlette debug helpers in production so the process stays
    # small and we do not spend RAM on extra middleware/logging we do not need.
    DEBUG: bool = False
    # Server bind for this VM deploy.
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    # If you put a reverse proxy/load balancer in front, list its origin(s)
    # here instead of the wildcard. Leave "*" for direct dev exposure only.
    ALLOWED_ORIGINS: list[str] = ["*"]
    # Trusted proxy count for X-Forwarded-For when behind a proxy.
    PROXY_COUNT: int = 0
    # If your platform injects a PORT env var, prefer it over the default above.
    # The app still defaults to 8000 if PORT is absent.
    # Optional env var for deployments that inject a dynamic port (e.g. some
    # platform dashboards). Settings still defaults to 8000 if PORT is absent.

    # ── File uploads ───────────────────────────────────────────────────────────
    # Keep uploads on the same partition as the database on this low-disk VM.
    UPLOAD_DIR: str = "./uploads"
    # 20 MB is generous for invoices/audio; lower this if disk is tight.
    MAX_FILE_SIZE_MB: int = 20
    # Auto-prune uploads older than this many days (0 = disabled).
    UPLOAD_PRUNE_AGE_DAYS: int = 0
    # Local offline voice path for the low-resource VM.
    # When false, the voice route runs in demo/stub mode (no transcription).
    # When true, it tries a tiny local ASR model if one is installed.
    USE_LOCAL_ASR: bool = False
    # How many negotiation session objects to keep in memory before pruning.
    # In-memory session cache is fine for this single-VM deploy; keep the cap
    # conservative so RAM is left for uvicorn + Postgres client.
    NEGOTIATION_SESSION_CACHE_MAX: int = 50


settings = Settings()
