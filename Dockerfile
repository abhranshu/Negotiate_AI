# NegotiateAI — Railway Deployment Dockerfile
# Stack: Python 3.11 + FastAPI + Uvicorn (Gunicorn workers)
# NO GPU needed — Whisper runs on Groq API, ML models are pre-trained PKL files

FROM python:3.11-slim

# ── System dependencies ────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ──────────────────────────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies ────────────────────────────────────────────────
COPY requirements_deploy.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements_deploy.txt

# ── Copy project files ─────────────────────────────────────────────────────────
COPY api/           ./api/
COPY models/        ./models/
COPY outcome_prediction.py   .
COPY negotiation_ai.py       .
COPY settlement_generator.py .
COPY voice_pipeline.py       .
COPY translation_service.py  .
COPY document_intelligence.py .
COPY data/msme_samadhaan.csv ./data/

# ── Create uploads directory ───────────────────────────────────────────────────
RUN mkdir -p uploads

# ── Expose port ────────────────────────────────────────────────────────────────
EXPOSE 8000

# ── Health check ───────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ── Start command (Gunicorn + Uvicorn workers for concurrency) ────────────────
# 2 workers = good for Railway's 512MB-1GB RAM containers
CMD ["gunicorn", "api.main:app", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--access-logfile", "-"]
