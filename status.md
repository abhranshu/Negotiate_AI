# NegotiateAI (MSME Major Project) - Current Status

> **Last Updated:** 2026-08-10 | **True Completion: ~85%**
> *(Previous estimate of 60% was based on outdated documentation)*

---

## 1. Project Overview
**NegotiateAI** — An AI-powered Online Dispute Resolution (ODR) platform for MSME payment disputes under the MSMED Act 2006.

**Tech Stack:**
- **AI/ML**: Python (Whisper, DistilBERT, RoBERTa, XGBoost, LightGBM, SHAP)
- **Backend**: FastAPI + SQLAlchemy + SQLite (dev) / PostgreSQL (prod)
- **Frontend Web**: React 18 + MUI + Axios + WebSockets
- **Mobile**: Kotlin + Jetpack Compose + Retrofit (Android)

---

## 2. Phase-by-Phase Status

### ✅ PHASE 1 — Core AI/ML Intelligence (100% Done)
All 5 standalone AI modules are complete and functional:

| Module | File | Status |
|--------|------|--------|
| Voice Pipeline | `AIML/voice_pipeline.py` | ✅ Done |
| Document Intelligence | `AIML/document_intelligence.py` | ✅ Done |
| Outcome Prediction | `AIML/outcome_prediction.py` | ✅ Done |
| Negotiation AI | `AIML/negotiation_ai.py` | ✅ Done |
| Settlement Generator | `AIML/settlement_generator.py` | ✅ Done |

The `AIML/` folder packages all modules as a proper Python package (with `__init__.py`) for clean API imports.

---

### ✅ PHASE 2 — Backend API & Database (100% Done)
Full FastAPI backend with all routes wired to AI modules:

| File | Purpose | Status |
|------|---------|--------|
| `api/main.py` | App entry, CORS, lifespan startup | ✅ |
| `api/config.py` | Settings/env config | ✅ |
| `api/database.py` | SQLAlchemy engine (SQLite default) | ✅ |
| `api/auth.py` | JWT token helper | ✅ |
| `api/websockets.py` | WebSocket Connection Manager | ✅ |
| `api/models/user.py` | User DB model | ✅ |
| `api/models/case.py` | Case, Document, Message DB models | ✅ |
| `api/routes/auth.py` | Register / Login / Profile | ✅ |
| `api/routes/cases.py` | Case CRUD | ✅ |
| `api/routes/documents.py` | Document upload | ✅ |
| `api/routes/voice_groq.py` | Voice intake via Groq API | ✅ |
| `api/routes/predict.py` | Outcome prediction endpoint | ✅ |
| `api/routes/negotiate.py` | WebSocket chat + AI mediator | ✅ |
| `api/routes/settlement.py` | Settlement generation | ✅ |

**Demo:** `python demo_phase2.py` runs full end-to-end smoke test.

---

### ✅ PHASE 3 — Real-Time WebSocket Engine (~95% Done)
| Feature | Status |
|---------|--------|
| `/ws/{case_id}` WebSocket endpoint | ✅ Done |
| Connection Manager (broadcast + private channels) | ✅ Done |
| Real-time sentiment analysis on messages | ✅ Done |
| Private AI suggestions per party | ✅ Done |
| **Redis pub/sub state management** | ❌ Not done (in-memory only) |

---

### ✅ PHASE 4 — Frontend Web App (~90% Done)
> ⚠️ **`phases.md` incorrectly listed this as "Not Started" — all 8 components exist.**

| Component | File | Status |
|-----------|------|--------|
| Auth (Login/Register) | `AuthScreen.jsx` | ✅ |
| Case Dashboard | `CaseDashboard.jsx` | ✅ |
| Case Detail View | `CaseDetail.jsx` | ✅ |
| Create Case Form | `CreateCase.jsx` | ✅ |
| Negotiation Chat Room | `NegotiationChat.jsx` | ✅ |
| Prediction Panel | `PredictionPanel.jsx` | ✅ |
| Settlement Preview | `SettlementPanel.jsx` | ✅ |
| Shared UI Primitives | `UI.jsx` | ✅ |
| API client config | `api.js` + `theme.js` | ✅ |

**Stack:** React 18, react-scripts 5, Axios, MUI  
**Run:** `cd frontend && npm start`

---

### 🟡 BONUS — Android App (Kotlin) (Unknown % — Needs Testing)
> Not mentioned in any phase docs, but the project exists.

| Item | Status |
|------|--------|
| Gradle project setup | ✅ |
| `app/build.gradle.kts` (Compose + Retrofit + Navigation) | ✅ |
| `AndroidManifest.xml` | ✅ |
| Kotlin source (`com/negotiateai/app`) | ✅ exists |
| Build tested / APK generated | ❓ Unknown |

---

## 3. Remaining Gaps

| Gap | Priority |
|-----|----------|
| **Redis** — replace in-memory WS dict with Redis pub/sub | 🔴 High |
| **Frontend testing** — run `npm start`, fix any runtime bugs | 🔴 High |
| **Android app** — assess completion, test build | 🟡 Medium |
| **PostgreSQL** — swap SQLite for production database | 🟡 Medium |
| **Alembic migrations** — proper schema versioning | 🟡 Medium |
| **Model fine-tuning** — train on actual MSME/Indian legal data | 🟡 Medium |
| **RBAC** — enforce Claimant / Respondent / Admin permissions | 🟡 Medium |
| **CORS hardening** — restrict `allow_origins=["*"]` for production | 🟠 Low |
| **RTI data** — acquire real MSME Samadhan dataset | 🟠 Low |

---

## 4. How to Run

```bash
# Backend
uvicorn api.main:app --reload --port 8000
# API Docs: http://localhost:8000/docs

# Frontend
cd frontend && npm start
# Web App: http://localhost:3000

# Demo smoke test
python demo_phase2.py
```

---

## 5. Summary

| Phase | Documented | Actual |
|-------|-----------|--------|
| Phase 1 — AI/ML | ✅ Done | ✅ Done |
| Phase 2 — Backend | ✅ Done | ✅ Done |
| Phase 3 — WebSockets | 🟡 In Progress | ✅ ~95% (Redis only missing) |
| Phase 4 — Frontend | ❌ Not Started | ✅ ~90% Built |
| Android App | ❌ Not Mentioned | 🟡 Exists, untested |
| **Overall** | **~60%** | **~85%** |
