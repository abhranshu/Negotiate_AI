# 📁 Important Files Map: NegotiateAI

This document provides an exhaustive list of every essential file that builds and runs the **NegotiateAI** project, organized by architectural layer.

---

## 🧠 1. Standalone AI & ML Core Modules (Phase 1)

- **[`voice_pipeline.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/voice_pipeline.py)** — **Module 1**: Audio transcription (Whisper ASR), IndicTrans2 multilingual translation, and SpaCy/BERT NER entity extraction to auto-fill case forms from voice notes.
- **[`document_intelligence.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/document_intelligence.py)** — **Module 2**: Tesseract OCR for scanned invoices/POs, DistilBERT document classification into 8 categories, evidence gap analysis, and case summarization.
- **[`outcome_prediction.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/outcome_prediction.py)** — **Module 3**: XGBoost & LightGBM ensemble predicting settlement probability, settlement amount range, ZOPA (Zone of Possible Agreement), and SHAP explainability values.
- **[`negotiation_ai.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/negotiation_ai.py)** — **Module 4**: RoBERTa sentiment analysis, Nash Bargaining & Rubinstein game-theory bargaining engines, and Mistral-7B LLM mediator logic.
- **[`settlement_generator.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/settlement_generator.py)** — **Module 5**: Automated MSMED Act 2006 compliant legal PDF generator using ReportLab and a rule-based legal validator.
- **[`translation_service.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/translation_service.py)** — Multilingual translation utility wrapper supporting IndicTrans2 and fallbacks.
- **[`download_indictrans2.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/download_indictrans2.py)** — Model downloader script for fetching IndicTrans2 weights.

---

## 🌐 2. Backend API Infrastructure (Phase 2 & Phase 3)

- **[`api/main.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/main.py)** — FastAPI application entry point, CORS middleware, lifespan events (table creation), and router registrations.
- **[`api/config.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/config.py)** — Configuration settings powered by Pydantic (`.env` reader).
- **[`api/database.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/database.py)** — SQLAlchemy database engine setup, session factory (`SessionLocal`), and `get_db` dependency.
- **[`api/auth.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/auth.py)** — Security module handling bcrypt password hashing, JWT token generation, and `get_current_user` auth guard.
- **[`api/websockets.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/websockets.py)** — `ConnectionManager` class handling real-time WebSocket connection pools, public room broadcasts, and private party-specific AI strategy hints.

---

## 🗄️ 3. Database Models (`api/models/`)

- **[`api/models/__init__.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/models/__init__.py)** — Models package exporter.
- **[`api/models/user.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/models/user.py)** — SQLAlchemy ORM schema for `User` table (`id`, `email`, `hashed_password`, `full_name`, `role`).
- **[`api/models/case.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/models/case.py)** — SQLAlchemy ORM schemas for `Case`, `Document`, and `Message` tables.

---

## 📋 4. Request & Response Schemas (`api/schemas/`)

- **[`api/schemas/__init__.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/schemas/__init__.py)** — Schemas package exporter.
- **[`api/schemas/user.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/schemas/user.py)** — Pydantic schemas for user registration, login, and auth response tokens.
- **[`api/schemas/case.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/schemas/case.py)** — Pydantic schemas for cases, documents, predictions, chat messages, and settlement outputs.

---

## 🛣️ 5. API Routers (`api/routes/`)

- **[`api/routes/__init__.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/routes/__init__.py)** — Routers package exporter.
- **[`api/routes/auth.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/routes/auth.py)** — Endpoints for user registration (`/auth/register`), login (`/auth/login`), and profile (`/auth/me`).
- **[`api/routes/cases.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/routes/cases.py)** — Endpoints for creating and retrieving dispute cases (`/api/cases`).
- **[`api/routes/documents.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/routes/documents.py)** — Endpoints for uploading legal documents, OCR processing, and document classification (`/api/cases/{id}/documents`).
- **[`api/routes/voice.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/routes/voice.py)** — Endpoints for uploading audio notes and auto-filling dispute forms (`/api/cases/voice`).
- **[`api/routes/predict.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/routes/predict.py)** — Endpoints for running ML outcome prediction and ZOPA calculations (`/api/cases/{id}/predict`).
- **[`api/routes/negotiate.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/routes/negotiate.py)** — REST (`POST /negotiate`) & Real-time WebSocket (`WS /ws/{case_id}`) endpoints for live 3-party negotiation.
- **[`api/routes/settlement.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/api/routes/settlement.py)** — Endpoints for generating and downloading final MSMED Act settlement PDFs (`/api/cases/{id}/settlement`).

---

## ⚙️ 6. Driver & Verification Scripts

- **[`demo.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/demo.py)** — Prototype verification script for testing Phase 1 AI modules standalone in terminal.
- **[`demo_phase2.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/demo_phase2.py)** — End-to-end backend smoke test script verifying FastAPI endpoints, auth, DB persistence, and ML integration.

---

## 📄 7. Environment & Configuration Files

- **[`.env`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/.env)** — Local environment variable secrets (Database URL, JWT Secret, algorithm).
- **[`requirements.txt`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/requirements.txt)** — Dependencies for Phase 1 AI/ML modules (Whisper, RoBERTa, XGBoost, ReportLab).
- **[`requirements_api.txt`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/requirements_api.txt)** — Dependencies for FastAPI web server, SQLAlchemy, Uvicorn, and Auth.

---

## 📑 8. Project Documentation & AI Context Files

- **[`README.md`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/README.md)** — Main project documentation overview, system architecture diagram, tech stack, and setup guide.
- **[`phases.md`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/phases.md)** — Project roadmap tracking status of Phases 1 to 4.
- **[`status.md`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/status.md)** — Comprehensive status report & gap analysis.
- **[`information.md`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/information.md)** — Complete AI context file detailing system architecture, user journeys, data flow, monorepo layout, and deployment strategy.
- **[`BUILD_PROMPT.md`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/BUILD_PROMPT.md)** — Master build prompt containing exact technical requirements and code guidelines.
- **[`DATA_SOURCES.md`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/DATA_SOURCES.md)** — Comprehensive guide on training datasets and data acquisition strategies for all 5 AI modules.
- **[`AGENTS.md`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/AGENTS.md)** — AI agent rules and tool usage instructions.
