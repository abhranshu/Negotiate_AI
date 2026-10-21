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
    LOCAL_MODEL_ID: str = "Qwen/Qwen2.5-1.5B-Instruct"
    # int8-dynamic-quantize the model on CPU.
    #
    # MEASURED: leave this FALSE. On Qwen2.5-1.5B-Instruct with the mediator
    # prompt (same seed-independent sampling settings), the int8 path produced
    # incoherent scraped-web text in 4/4 runs and took 140-155s per 96 tokens,
    # while the unquantized bf16 path produced a coherent mediator reply in
    # 34s on the identical prompt. int8 here costs quality *and* speed, and
    # loading fp32 first (required, since the oneDNN int8 op rejects bf16
    # input) peaks at ~9.2 GB — which OOM-killed the container. bf16 loads in
    # ~3 GB, so the default path also fixes the crash-loop.
    # Only re-enable if you re-measure on your target CPU.
    # Applied on CPU only; ignored on CUDA (fp16 already wins there).
    LOCAL_MODEL_QUANTIZE: bool = False
    # Where the local model runs: auto | cuda | cpu.
    #   auto — GPU when CUDA is available. accelerate spills whatever does not
    #          fit in VRAM to CPU, which keeps working but is much slower.
    #   cuda — GPU only. Fails loudly instead of silently spilling to CPU, so you
    #          never have to guess whether the GPU is actually being used.
    #   cpu  — ignore the GPU entirely (int8 quantized, see LOCAL_MODEL_QUANTIZE).
    LOCAL_MODEL_DEVICE: str = "auto"
    # Cap on generated tokens per mediator turn. The system prompt asks for 2-4
    # sentences, so a bigger cap only lengthens the worst-case wait — and with
    # any layers spilled to CPU that wait is what makes the chat look hung.
    LOCAL_MODEL_MAX_NEW_TOKENS: int = 128

    # ── AWS Bedrock (Nova Micro default) ─────────────────────────────────────
    # USE_BEDROCK=true routes the mediator + document review through Bedrock
    # (fast, ~1-2s) instead of the local HF model (slow on CPU, 30-150s).
    # Model IDs are inference-profile safe: "amazon.nova-micro-v1:0" works
    # today; swap to "us.anthropic.claude-haiku-4-5-20251001-v1:0" via env
    # once Anthropic Marketplace access is enabled on the account.
    USE_BEDROCK: bool = False
    AWS_REGION_BEDROCK: str = "us-east-1"
    BEDROCK_MEDIATOR_MODEL: str = "amazon.nova-micro-v1:0"
    BEDROCK_DOC_MODEL: str = "amazon.nova-micro-v1:0"
    BEDROCK_MAX_TOKENS: int = 400

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

    # ── Caching ────────────────────────────────────────────────────────────────
    # Each authenticated request normally does one `SELECT` of the user row, and
    # in the deployed setup the database is remote (Supabase pooler), so that is
    # a full network round-trip per request. Cache the row for this many seconds.
    #
    # This is user-specific data, so the TTL is deliberately short and any
    # endpoint that writes a user row must call api.auth.invalidate_user_cache().
    # Set to 0 to disable the cache entirely (every request hits the DB).
    AUTH_USER_CACHE_TTL_SECONDS: float = 60.0
    # Hard cap on cached user rows. When full, expired entries are dropped
    # first, then the oldest-inserted entry.
    AUTH_USER_CACHE_MAX: int = 512


settings = Settings()
