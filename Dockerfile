# NegotiateAI — Railway Deployment Dockerfile
# Stack: Python 3.11 + FastAPI + Uvicorn (Gunicorn workers)
# NO GPU needed — Whisper runs on Groq API, ML models are pre-trained PKL files

FROM python:3.11-slim

# ── System dependencies ────────────────────────────────────────────────────────
# curl           → HEALTHCHECK
# tesseract-ocr  → Module 2 document OCR (pytesseract needs the binary)
# poppler-utils  → pdf2image shell-out to pdftoppm; without it EVERY PDF upload
#                  fails OCR ("Unable to get page count. Is poppler installed?")
# fonts-noto     → non-ASCII glyphs for OCR (Hindi/Tamil/etc.)
# (gcc/g++/libpq-dev removed: all Python deps ship prebuilt wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-tam \
    poppler-utils \
    fonts-noto \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ──────────────────────────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies ────────────────────────────────────────────────
# NO torch / transformers / whisper (~2GB saved) — the Bedrock path (Nova Micro
# via boto3) replaces the local LLM, and heavy ML imports are lazy in AIML/.
COPY requirements_deploy.txt .
RUN pip install --no-cache-dir --upgrade pip && \
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
# RAG corpus (data/legal) is copied so the legal retriever works inside the
# container. data/chroma is NOT copied from the host: the index is rebuilt
# HERE with the same ONNX embeddings the runtime uses (host index was built
# with a different embedding model and would silently return garbage).
COPY data/legal             ./data/legal/
RUN PYTHONPATH=/app python -m AIML.legal_rag --build
# The build also downloads the ~80MB ONNX embedding model to /root/.cache/
# (same HOME at runtime) and writes data/chroma/keyword_corpus.json — so the
# container starts with vector search warm and a keyword fallback ready.

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
# Probe $PORT, not a hardcoded 8000: platforms that inject PORT (Railway, ECS,
# App Runner, Cloud Run) make the app bind that port, so probing 8000 would
# always fail and mark a working container unhealthy.
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD curl -f "http://localhost:${PORT:-8000}/health" || exit 1

# ── Start command (Gunicorn + Uvicorn workers for concurrency) ────────────────
# Default to ONE worker. Every gunicorn worker is a separate process and loads
# its own copy of PyTorch + the local Qwen model (~1.5-2 GB with int8). More
# than one worker on a memory-tight host causes an OOM kill. Override with
# WORKERS=N only after measuring peak RAM on the target instance.
# Bind to $PORT when set (Railway/ECS/App Runner), otherwise 8000 (local).
CMD ["sh", "-c", "gunicorn api.main:app --workers ${WORKERS:-1} --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --timeout 300 --keep-alive 5 --access-logfile -"]
