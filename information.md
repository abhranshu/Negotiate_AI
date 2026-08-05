# Comprehensive Project Context: NegotiateAI

**NegotiateAI** is a full-stack, real-time AI legal co-pilot and Online Dispute Resolution (ODR) platform built specifically for Micro, Small, and Medium Enterprises (MSMEs) in India dealing with delayed payment disputes. 

Instead of acting as a standard 1-on-1 chatbot, it functions as an intelligent, emotionally-neutral **AI mediator** connecting two human parties: a **Claimant** (MSME supplier/creditor) and a **Respondent** (buyer/debtor). It grounds all legal guidance strictly in the **Indian MSMED Act 2006** (Sections 15–23), the **Indian Contract Act 1872**, and past MSEFC (Micro and Small Enterprises Facilitation Council) case precedents.

---

## 🎯 What We Are Trying To Do

The primary goal is to resolve MSME payment disputes faster (days instead of 2–5 years) and significantly cheaper than traditional legal routes (expensive lawyers and court backlogs).

- **Voice/Multilingual Filing**: Allow non-English speaking MSME owners to file disputes using voice notes in native Indian languages (Hindi, Tamil, Telugu, etc.).
- **Document Processing**: Automatically scan, classify, and extract data from invoices, POs, and contracts, performing gap analysis for missing evidence.
- **Data-Driven Predictions**: Give both parties an objective calculation of settlement probability, expected settlement range (₹), ZOPA (Zone of Possible Agreement), and estimated tribunal resolution time using XGBoost/LightGBM + SHAP.
- **Real-Time Live Negotiation**: Provide a 3-actor WebSocket negotiation room where Claimant and Respondent chat live while the AI mediator analyzes sentiment, computes game-theoretic bargaining options (Nash & Rubinstein), and provides *private, party-specific* strategy suggestions.
- **Automated Binding Settlement**: Draft a legally valid, court-admissible settlement agreement (PDF) automatically upon agreement.

---

## 👥 User Roles & User Journey Flow

### Roles
1. **Claimant**: The MSME business owner seeking recovery of unpaid dues.
2. **Respondent**: The corporate/buyer entity owing the payment.
3. **AI Mediator**: System actor observing the live channel, intervening on hostility, providing private advice, and enforcing legal/game-theoretic boundaries.

### Step-by-Step User Journey
1. **Case Intake (Claimant)**: Uploads audio description or documents -> Voice Pipeline (Whisper + IndicTrans2 + SpaCy NER) & Document Intelligence (Tesseract OCR + DistilBERT) populate case metadata.
2. **Case Assessment**: System runs Outcome Prediction Engine -> Generates ZOPA, predicted settlement range, and settlement probability.
3. **Invitation (Respondent)**: Respondent receives notification/link to join the dispute session.
4. **Negotiation Room (Live Chat)**:
   - Both parties enter a 3-panel UI.
   - Live messages pass through `negotiation_ai.py` (RoBERTa sentiment analysis + Nash/Rubinstein models + Mistral-7B LLM).
   - Public chat displays neutral mediator interventions; private sidebars give confidential strategic tips to each side.
5. **Agreement & Settlement**: When consensus is reached, `settlement_generator.py` compiles the terms into an MSMED-compliant PDF, ready for e-signing.

---

## 🔄 AI Module Interaction Data Flow

```text
[Audio Input / Scanned Docs]
       │
       ├──► Voice Pipeline (Whisper + IndicTrans2 + SpaCy NER) ────────┐
       │                                                                ▼
       └──► Document Intelligence (Tesseract OCR + DistilBERT) ───► [Case Metadata / Structured Record]
                                                                        │
                                                                        ▼
                                                        Outcome Prediction Engine
                                                      (XGBoost + LightGBM + SHAP)
                                                                        │
                                                                        ▼
                                                          [ZOPA & Outcome Baseline]
                                                                        │
                                                                        ▼
                                                          Real-Time Negotiation AI
                                                  (RoBERTa Sentiment + Nash Bargaining + Mistral-7B)
                                                                        │
                                                                        ▼
                                                           Settlement Generator
                                                      (ReportLab PDF + Legal Validator)
```

---

## 📊 How Much Work Is Done (~60%)

### Phase 1: Core AI & ML Intelligence — **100% COMPLETE**
- [x] `voice_pipeline.py`: Whisper speech-to-text, IndicTrans2 translation, SpaCy + BERT NER entity extraction.
- [x] `document_intelligence.py`: Tesseract OCR, DistilBERT document classification (8 classes), evidence gap analysis.
- [x] `outcome_prediction.py`: XGBoost & LightGBM ensemble for settlement probability, ZOPA calculation, and SHAP explainability.
- [x] `negotiation_ai.py`: RoBERTa hostility/sentiment detection, Nash Bargaining & Rubinstein game-theory models, Mistral-7B LLM mediator prompt generator.
- [x] `settlement_generator.py`: MSMED Act template generator, rule-based legal validator, ReportLab PDF rendering engine.

### Phase 2: Backend API & Database Architecture — **DEMO READY**
- [x] FastAPI web server initialization (`api/main.py`, `api/config.py`).
- [x] Database architecture (`api/database.py`) with SQLite auto-creation for quick demos.
- [x] SQLAlchemy models (`api/models/`): `User`, `Case`, `Document`, `Message`.
- [x] Pydantic request/response schemas (`api/schemas/`).
- [x] REST routes (`api/routes/`): `auth.py`, `cases.py`, `documents.py`, `voice.py`, `predict.py`.
- [x] Demo proof-of-concept script: `python demo_phase2.py`.

---

## ⏳ What Remains To Be Done (~40%)

### Phase 3: Real-Time Communication Engine — **PENDING**
- [ ] WebSocket endpoint: `WS /ws/negotiation/{session_id}` in FastAPI.
- [ ] Redis integration for managing active connection states, pub/sub channels, and message queues.
- [ ] Private AI suggestion sub-channels (party-isolated WebSockets).
- [ ] Deadlock detection handler (proactive proposal after 5 mins of inactivity).

### Phase 4: Frontend Web Application — **PENDING**
- [ ] Vite + React 18 + TypeScript + TailwindCSS application setup.
- [ ] Auth UI (Login / Register).
- [ ] Dashboard (Active cases, predictions, deadlines).
- [ ] Filing Wizard (Voice recording upload, document upload, review).
- [ ] Negotiation Room (3-panel UI: Left = Case Info & ZOPA; Center = Live Chat; Right = Private AI Tips).
- [ ] Settlement Preview & e-Sign interface.

### Data & Model Fine-Tuning — **PENDING**
- [ ] Collect real MSEFC case data (RTI requests filed).
- [ ] Fine-tune base models (Mistral-7B, DistilBERT, Whisper) on domain-specific Indian legal datasets.

---

## 🗄️ Database Schema & Models (`api/models/`)

- **User**: `id`, `email`, `hashed_password`, `full_name`, `role` (Claimant / Respondent / Admin), `created_at`.
- **Case**: `id`, `claimant_id`, `respondent_id`, `dispute_type`, `claimed_amount`, `agreed_amount`, `status` (FILING, NEGOTIATING, SETTLED, CLOSED), `created_at`.
- **Document**: `id`, `case_id`, `filename`, `file_path`, `doc_type` (Invoice, PO, Contract, etc.), `ocr_text`, `uploaded_at`.
- **Message**: `id`, `case_id`, `sender_id` (User or AI Mediator), `content`, `sentiment_score`, `hostility_score`, `is_private`, `target_role`, `timestamp`.

---

## 🌐 API Endpoint Map

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register new user |
| `POST` | `/auth/login` | Login and receive JWT access token |
| `POST` | `/cases/` | Create a new dispute case |
| `GET` | `/cases/` | List user cases |
| `POST` | `/voice/process` | Upload audio note → transcribe + extract entities |
| `POST` | `/documents/upload` | Upload PDF/image → OCR + document classification |
| `POST` | `/predict/outcome` | Run XGBoost/LightGBM to get settlement range & ZOPA |
| `POST` | `/negotiation/message` | Process single chat message through AI mediator |
| `POST` | `/settlement/generate` | Build MSMED Act compliant PDF settlement |
| `WS` | `/ws/negotiation/{session_id}` | *(Phase 3)* Real-time bi-directional chat & private advice |

---

## 🔑 Key Environment Variables (`.env`)

```env
DATABASE_URL=sqlite+aiosqlite:///./phase2_demo.db # Or postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your_jwt_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
OPENAI_API_KEY=your_openai_key_if_using_api
HUGGINGFACE_HUB_TOKEN=your_hf_token
```

---

## 📂 Current vs. Desired File Structure

### Current Structure
```text
MSME Major project/
├── .env, requirements.txt, requirements_api.txt
├── demo.py, demo_phase2.py
├── voice_pipeline.py
├── document_intelligence.py
├── outcome_prediction.py
├── negotiation_ai.py
├── settlement_generator.py
├── api/
│   ├── main.py, config.py, database.py, auth.py
│   ├── models/ (user.py, case.py, document.py, message.py)
│   ├── schemas/ (user.py, case.py, document.py, message.py)
│   └── routes/ (auth.py, cases.py, documents.py, voice.py, predict.py)
├── data/
├── models/
├── output/
└── uploads/
```

### Desired Monorepo Production Structure
```text
negotiate-ai/
├── frontend/                   ← Phase 4 (React + Vite + TypeScript + Tailwind)
│   ├── src/
│   │   ├── components/         ← Reusable UI (Chat, Forms)
│   │   ├── pages/              ← Dashboard, Room, Filing
│   │   ├── hooks/              ← WebSockets & API hooks
│   │   ├── store/              ← Zustand / Redux state
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                    ← Phase 2 & 3 (FastAPI)
│   ├── app/
│   │   ├── main.py             ← Entrypoint
│   │   ├── core/               ← Config, Security, DB session
│   │   ├── api/                ← REST Routers
│   │   ├── websockets/         ← WebSocket handlers (Phase 3)
│   │   ├── models/             ← SQLAlchemy Models
│   │   └── schemas/            ← Pydantic schemas
│   ├── tests/
│   ├── alembic/                ← Migrations
│   └── requirements.txt
│
├── ml_service/                 ← Phase 1 (AI Pipeline Scripts)
│   ├── pipelines/              
│   │   ├── voice.py
│   │   ├── document.py
│   │   ├── prediction.py
│   │   ├── negotiation.py
│   │   └── settlement.py
│   ├── models_cache/           ← Local model weights
│   └── requirements_ml.txt
│
└── infrastructure/             ← Deployment configs & Dockerfiles
    ├── docker-compose.yml
    ├── Dockerfile.frontend
    ├── Dockerfile.backend
    └── Dockerfile.ml
```

---

## 🚀 How to Run the Project Locally

### 1. Run Core AI Standalone Scripts (Phase 1)
```bash
python voice_pipeline.py
python document_intelligence.py
python outcome_prediction.py
python negotiation_ai.py
python settlement_generator.py
```

### 2. Run End-to-End Backend Demo (Phase 2)
```bash
python demo_phase2.py
```

### 3. Run FastAPI Web Server
```bash
uvicorn api.main:app --reload --port 8000
# OpenAPI Docs: http://localhost:8000/docs
```

---

## ☁️ Production Deployment Strategy

1. **Database & Redis**:
   - Managed PostgreSQL (Supabase / Neon / AWS RDS).
   - Managed Redis (Upstash / Redis Cloud / AWS ElastiCache) for WebSocket pub/sub and state caching.
2. **Backend Web Server (FastAPI)**:
   - Deploy as a Docker container on Render, Railway, or DigitalOcean App Platform (ensuring WebSocket sticky connections).
3. **ML Inference Pipeline**:
   - **Option A (Monolithic)**: GPU-enabled EC2 / RunPod instance hosting heavy models (Whisper, RoBERTa, Mistral).
   - **Option B (Serverless GPU)**: Host model endpoints on Modal.com, Baseten, or Replicate to reduce idle costs.
4. **Frontend (React)**:
   - Build static assets via Vite (`npm run build`) and deploy to Vercel, Netlify, or AWS S3 + CloudFront.
