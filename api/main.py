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

# Import all models so SQLAlchemy registers them before create_all()
import api.models  # noqa: F401

from api.routes.auth       import router as auth_router
from api.routes.cases      import router as cases_router
from api.routes.documents  import router as documents_router
from api.routes.voice      import router as voice_router
from api.routes.predict    import router as predict_router
from api.routes.negotiate  import router as negotiate_router
from api.routes.settlement import router as settlement_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables and upload directory on startup."""
    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    print("✅ Database tables created / verified")
    print(f"✅ Upload directory: {settings.UPLOAD_DIR}")
    yield
    print("🛑 Shutting down NegotiateAI API")


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
