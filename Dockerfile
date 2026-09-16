# NegotiateAI — Railway Deployment Dockerfile
# Stack: Python 3.11 + FastAPI + Uvicorn (Gunicorn workers)
# NO GPU needed — Whisper runs on Groq API, ML models are pre-trained PKL files

FROM python:3.11-slim

# ── System dependencies ────────────────────────────────────────────────────────
# libpq-dev      → psycopg2-binary / PostgreSQL driver
# curl           → HEALTHCHECK
# tesseract-ocr  → Module 2 document OCR (pytesseract needs the binary)
# fonts-noto     → non-ASCII glyphs for OCR (Hindi/Tamil/etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-tam \
    fonts-noto \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ──────────────────────────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies ────────────────────────────────────────────────
COPY requirements_deploy.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements_deploy.txt

# ── Copy project files ─────────────────────────────────────────────────────────
# Note: ML modules live in AIML/ (packaged). Root translation_service.py is
# imported by AIML/voice_pipeline.py — both must be copied.
COPY api/                   ./api/
COPY AIML/                  ./AIML/
COPY models/                ./models/
COPY alembic.ini            .
COPY translation_service.py .
# Training data not copied — models use pre-trained .pkl files at runtime
# RAG corpus (data/legal) + chroma index are copied so the legal retriever
# works inside the container:
COPY data/legal             ./data/legal/
COPY data/chroma            ./data/chroma/

# ── Create uploads directory ───────────────────────────────────────────────────
RUN mkdir -p uploads data

# ── Expose port ────────────────────────────────────────────────────────────────
# Railway injects $PORT at runtime (default 8000 locally)
EXPOSE 8000

# ── Environment ────────────────────────────────────────────────────────────────
# Make the project root importable so `from AIML.x import ...` and
# `translation_service` resolve regardless of CWD.
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# ── Health check ───────────────────────────────────────────────────────────────
# start-period=180s: local LLM + int8 quantization may take a few minutes at boot
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ── Start command (Gunicorn + Uvicorn workers for concurrency) ────────────────
# 2 workers = good for Railway's 512MB-1GB RAM containers
# Bind to $PORT when set (Railway), otherwise 8000 (local/HEALTHCHECK).
CMD ["sh", "-c", "gunicorn api.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --timeout 300 --keep-alive 5 --access-logfile -"]
