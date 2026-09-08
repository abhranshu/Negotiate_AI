"""
NegotiateAI — FastAPI application entry point.
Run with:  uvicorn api.main:app --reload --port 8000
Docs at:   http://localhost:8000/docs
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.database import engine, Base

# Import all models so Alembic can autogenerate and so the app can use them.
import api.models  # noqa: F401

from api.routes.auth       import router as auth_router
from api.routes.cases      import router as cases_router
from api.routes.documents  import router as documents_router
from api.routes.voice_groq  import router as voice_router
from api.routes.predict    import router as predict_router
from api.routes.negotiate  import router as negotiate_router
from api.routes.settlement import router as settlement_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run DB migrations, create upload directory, and pre-load ML models on startup."""
    # ── Run Alembic migrations so the DB schema is always up to date ─────
    # This replaces Base.metadata.create_all() which was unsafe for production
    # (no versioning, no rollback, silently ignores existing tables).
    try:
        from alembic.config import Config
        from alembic import command
        import os as _os

        # alembic.ini lives at the project root.
        project_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
        alembic_ini = _os.path.join(project_root, "alembic.ini")

        cfg = Config(alembic_ini)
        # Point Alembic at the same DB the app uses.
        cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL.strip())
        # Ensure project root is on sys.path so 'api' imports resolve in env.py.
        if project_root not in _os.environ.get("PYTHONPATH", ""):
            _os.environ["PYTHONPATH"] = project_root
        if project_root not in __import__("sys").path:
            __import__("sys").path.insert(0, project_root)

        command.upgrade(cfg, "head")
        print("[OK] Database migrations applied")
    except Exception as exc:
        print(f"[WARN] Alembic migration failed ({exc}) -- falling back to create_all")
        Base.metadata.create_all(bind=engine)
        print("[OK] Database tables created (fallback)")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    print(f"[OK] Upload directory: {settings.UPLOAD_DIR}")

    # ── Pre-load ML models so the first negotiation message is fast ────────
    # Without this, the first user message triggers a 1-2 min model load
    # that blocks all other requests on this worker.
    if settings.USE_LOCAL_MODEL:
        try:
            from AIML.negotiation_ai import _build_local_pipe
            print("⏳ Pre-loading LegalParam model (CPU, ~11GB)...")
            _build_local_pipe()
            print("✅ LegalParam model ready")
        except Exception as e:
            print(f"⚠️  LegalParam pre-load failed ({e}) — will retry on first message")

        # Pre-load sentiment model too (saves ~5-15s on first message)
        try:
            from AIML.negotiation_ai import NegotiationSentimentAnalyser
            print("⏳ Pre-loading sentiment model...")
            NegotiationSentimentAnalyser()
            print("✅ Sentiment model ready")
        except Exception as e:
            print(f"⚠️  Sentiment model pre-load failed ({e}) — will retry on first message")

    yield
    print("Shutdown NegotiateAI API")


app = FastAPI(
    title       = "NegotiateAI — MSME ODR Platform",
    description = (
        "AI-powered Online Dispute Resolution for MSME payment disputes "
        "under the MSMED Act 2006. Modules: Voice → Documents → Prediction → "
        "Negotiation → Settlement."
    ),
    version     = "0.1.0",
    lifespan    = lifespan,
)

# ── CORS (allow all origins in development; restrict in production) ────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Register all routers ───────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(cases_router)
app.include_router(documents_router)
app.include_router(voice_router)
app.include_router(predict_router)
app.include_router(negotiate_router)
app.include_router(settlement_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service":  "NegotiateAI API",
        "version":  "0.1.0",
        "status":   "running",
        "docs":     "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
