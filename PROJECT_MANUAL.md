# Project Manual — NegotiateAI

> **Full project reference for anyone reading this repo.** Use the table of contents below to find answers to any project-related question.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
1.5. [What This Project Is Doing](#15-what-this-project-is-doing)
1.6. [Primary Function of This Project](#16-primary-function-of-this-project)
1.7. [MVP (Minimum Viable Product) of This Project](#17-mvp-minimum-viable-product-of-this-project)
2. [Why this project exists](#2-why-this-project-exists)
3. [Who benefits](#3-who-benefits)
4. [Key differentiators (vs ChatGPT / generic AI)](#4-key-differentiators)
5. [Core AI Modules (Phase 1)](#5-core-ai-modules-phase-1)
6. [System Architecture](#6-system-architecture)
7. [Tech Stack](#7-tech-stack)
8. [Project Phases & Roadmap](#8-project-phases--roadmap)
9. [Current Status & Gap Analysis](#9-current-status--gap-analysis)
10. [Data Sources & Training Strategy](#10-data-sources--training-strategy)
11. [Project Structure](#11-project-structure)
12. [Setup & Installation](#12-setup--installation)
13. [API Reference (all endpoints)](#13-api-reference)
14. [Legal Foundation](#14-legal-foundation)
15. [How to Run (Local / Docker / Android / Web)](#15-how-to-run)
16. [Troubleshooting](#16-troubleshooting)
17. [Key File Reference (quick lookup)](#17-key-file-reference)

---

## 1. Project Overview

**NegotiateAI** is a full-stack, real-time **AI legal co-pilot and Online Dispute Resolution (ODR) platform** purpose-built for **Micro, Small, and Medium Enterprises (MSMEs)** dealing with **delayed payment disputes** in India.

Rather than a standard chatbot, NegotiateAI acts as an **intelligent AI mediator** that:

- Watches a **live text negotiation session** between two parties (a Claimant MSME and a Respondent Buyer)
- Continuously **analyzes the conversation** in real-time using sentiment and game-theory models
- **Cross-references uploaded legal documents** (invoices, purchase orders, contracts) against Indian law
- Provides **private, party-specific legal suggestions** grounded in **MSMED Act 2006** and past **MSEFC case precedents**
- **Automatically generates a legally binding settlement PDF** once both parties reach an agreement

The platform replaces expensive lawyers, slow courts, and emotionally charged face-to-face meetings with a fast, data-driven, and emotionally neutral dispute resolution process.

> **Domain context:** In India, delayed payments silently kill MSMEs. SIDBI MSME Pulse data shows over Rs.10.7 lakh crore in MSME receivables are delayed/stuck. Traditional legal routes are broken.

---

## 1.5 What This Project Is Doing

NegotiateAI is building an **AI-powered Online Dispute Resolution (ODR) platform** that helps small businesses in India solve payment disputes without going to court.

Here is what the project does, in plain terms:

1. **Lets a business owner upload invoices and contracts** — the AI reads them using OCR (optical character recognition).
2. **Lets a business owner record or upload a voice description** of the dispute — the AI transcribes it and pulls out key details like names, dates, and amounts.
3. **Predicts a fair settlement range** — based on similar past cases, the AI estimates how much money should be paid and how likely the claimant is to win.
4. **Acts as a neutral AI mediator** — during a live chat between the two parties, the AI suggests fair compromises and keeps the conversation constructive.
5. **Generates a legally valid settlement PDF** — once both sides agree, the AI drafts a formal agreement document ready to sign.

The goal is to replace expensive lawyers, years-long court battles, and stressful face-to-face arguments with a fast, affordable, and emotionally neutral digital process.

---

## 1.6 Primary Function of This Project

The **primary function** of NegotiateAI is to **resolve delayed payment disputes between MSMEs (small businesses) and their buyers through AI-mediated online negotiation**.

In one sentence: **NegotiateAI helps a small business get paid what it is owed, quickly and affordably, without needing a lawyer or going to court.**

This happens through a five-step pipeline:

| Step | What happens |
|------|-------------|
| 1. Voice/Documents | User uploads audio or paperwork describing the dispute |
| 2. Understanding | AI transcribes speech, reads documents, and extracts key facts |
| 3. Prediction | AI estimates a fair settlement amount and probability of success |
| 4. Negotiation | AI mediator chats with both parties to reach agreement |
| 5. Settlement | AI generates a legally binding PDF agreement |

Everything else (user accounts, case tracking, dashboards, mobile app) supports this core function.

---

## 1.7 MVP (Minimum Viable Product) of This Project

The **MVP** is the smallest version of NegotiateAI that still delivers real value. It includes only the features needed for a small business owner to resolve one delayed-payment dispute end to end.

### MVP includes:
- **User registration and login** (claimant and respondent)
- **Create a case** — enter dispute details manually or via voice upload
- **Outcome prediction** — see a predicted settlement range and win probability
- **AI-mediated negotiation chat** — a simple real-time chat where the AI suggests compromises
- **Settlement PDF generation** — download a basic agreement once both parties agree
- **Basic dashboard** — view your cases and their status

### MVP does NOT include (post-MVP features):
- Mobile Android app (web only in MVP)
- Multilingual voice support (English only in MVP)
- Document OCR/classification (manual entry only in MVP)
- Redis/scaling for many concurrent users
- Admin panel and role-based access control
- Postgres database (SQLite is fine for MVP)
- Real MSEFC case training data (synthetic data is fine for MVP)

> **MVP success metric:** A claimant can create a case, negotiate with the respondent through the AI mediator, reach agreement, and download a settlement PDF — all without a lawyer.

Delayed payments are a **silent killer for MSMEs in India**. NegotiateAI solves four compounding problems:

| Problem | Impact |
|---|---|
| **Too Expensive** | Hiring lawyers often costs more than the disputed amount itself |
| **Too Slow** | MSEFC arbitrations take 2-5 years due to massive backlogs |
| **Too Emotional** | Face-to-face negotiations break down due to ego and lack of legal knowledge |
| **Too Inaccessible** | Rural MSMEs lack access to legal expertise in their local language |

**NegotiateAI solves all four** by providing a fast, affordable (near-free), multilingual, and emotionally detached AI-powered resolution channel.

---

## 3. Who benefits

### Claimants (MSMEs)

- Recover stuck capital **in days instead of years**
- Get real-time legal advice grounded in the MSMED Act without hiring a lawyer
- Communicate in their **native Indian language** (Hindi, Tamil, Telugu, Bengali, etc.)
- Receive a **legally valid settlement PDF** automatically on agreement

### Respondents (Buyers / Large Corporations)

- Resolve disputes faster and at lower cost
- Get clear, party-specific legal guidance
## 4. Key differentiators (vs ChatGPT / generic AI)

| Generic AI chatbot | NegotiateAI |
|---|---|
| General-purpose text | Domain-specific legal ODR for MSMEs |
| No structure | Structured 5-module pipeline (Voice -> Documents -> Prediction -> Negotiation -> Settlement) |
| No stateful negotiation | Real-time 3-party negotiation (2 parties + AI mediator) |
| No legal grounding | Grounded in MSMED Act 2006 + MSEFC case precedents |
| No document processing | OCR + form-filling from uploads (invoices, POs, contracts) |
| Same response to everyone | Private, party-specific advice via WebSockets |
| No auto-generated legal document | Auto-drafts settlement PDF |


## 5. Core AI Modules (Phase 1)

| # | Module | File | Role |
|---|---|---|---|
| 1 | **Voice Pipeline** (ASR + NER) | `AIML/voice_pipeline.py` | Whisper transcription -> IndicTrans2 translation -> spaCy NER -> form fields |
| 2 | **Document Intelligence** (OCR + Classification) | `AIML/document_intelligence.py` | OCR extraction + DistilBERT document classification |
| 3 | **Outcome Prediction** (XGBoost/LightGBM) | `AIML/outcome_prediction.py` | Settlement ranges + settlement probability |
| 4 | **Negotiation AI** (Mediator) | `AIML/negotiation_ai.py` | RoBERTa sentiment + game-theoretic strategy + LLM moderator |
| 5 | **Settlement Generator** (Legal PDF) | `AIML/settlement_generator.py` | Auto-drafts MSMED-compliant settlement PDF |

All five modules are packaged under the `AIML/` package directory so the backend can import them cleanly.

---

## 6. System Architecture

```text
Client Apps (Android + Web)
        |
        | HTTPS
        v
FastAPI Backend (api/main.py)
  - CORS, JWT auth, DB models, Routers (auth, cases, documents, voice,
    predict, negotiate, settlement, report)
  - WebSocket manager for real-time chat
        |
        +-- AI Modules (AIML/): voice, documents, outcome, negotiation, settlement
        +-- Database: SQLAlchemy + SQLite/PostgreSQL
        +-- Cache: In-memory sessions, ML model cache
```

### End-to-end data flow

1. **Voice** -> `POST /voice` -> `voice_pipeline.py` -> NER -> pre-fills case fields
2. **Documents** -> `POST /documents` -> `document_intelligence.py` -> OCR + classify
3. **Predict** -> `POST /predict` -> `outcome_prediction.py` -> settlement range + probability
4. **Negotiate** -> WS `/ws/{id}` -> `negotiation_ai.py` -> private AI mediator per party
5. **Settlement** -> `POST /settlement` -> `settlement_generator.py` -> legal PDF

---

## 7. Tech Stack (in plain English)

| Part of app | Technology | What it does |
|---|---|---|
| AI & machine learning | Python, Whisper, spaCy, RoBERTa | Reads speech, understands text, detects emotions |
| Translation (Indian languages) | IndicTrans2 | Translates between English and Indian languages like Hindi, Tamil, Telugu |
| Predicting case outcomes | XGBoost / LightGBM | Estimates the likely settlement amount and chance of winning |
| Backend server | FastAPI, Python 3.10+ | Receives requests from the app and sends back responses |
| Database | SQLite (dev) / PostgreSQL (prod) | Stores users, cases, and negotiation history |
| User login & security | JWT (JSON Web Token) | Lets users log in securely and proves who they are |
| Web frontend (browser) | React 18, MUI, Axios | The website users see and interact with |
| Mobile app (Android) | Kotlin, Jetpack Compose, Retrofit | The Android app users install on their phone |
| Real-time chat | WebSockets | Lets two parties and the AI mediator chat live |
| Deployment | Docker | Packages the whole app so it runs the same everywhere |

## 8. Project Phases & Roadmap

| Phase | Status | Summary |
|---|---|---|
| Phase 1 - Core AI & ML | Done (100%) | Voice, documents, outcome, negotiation, settlement |
| Phase 2 - Backend API & DB | Done (demo-ready) | FastAPI, SQLAlchemy, JWT, all REST routes |
| Phase 3 - Real-Time WS | ~95% (Redis pending) | WS endpoint, manager, sentiment, private AI suggestions |
| Phase 4 - Web Frontend | ~90% Built | 8 components |
| Bonus - Android App | Untested | Exists, untested |

Overall documented: ~60%  |  Actual: ~85% |


## 9. What is done and what still needs work

### Done so far
- All 5 AI modules built (voice, documents, prediction, negotiation, settlement)
- Full FastAPI backend with all web routes working
- WebSocket real-time chat engine (95% ready, just needs Redis for scale)
- Web frontend about 90% built (8 screens/components)
- Android app exists in Kotlin but not yet tested

### High priority (fix first)
- **Redis** - switch from simple in-memory chat to Redis so many users can chat at once
- **Frontend testing** - open the website in a browser and fix any bugs

### Medium priority (fix next)
- **Android app** - build and test the APK on a real phone
- **PostgreSQL** - switch from SQLite (dev) to PostgreSQL (production database)
- **Database migrations** - use Alembic to track database changes over time
- **Train AI on real Indian legal data** - fine-tune models on actual MSME cases
- **User roles** - make sure Claimants, Respondents, and Admins see only what they should
- **Security** - lock down which websites can call the backend (CORS)

### Low priority (nice to have)
- **RTI data** - get real MSME Samadhan dataset through Right to Information request



## 10. Where the AI learns from (data sources)

Each AI module needs examples to learn from. Here is where those examples come from:

### Module 1 - Voice (listening to Indian languages)
- **AI4Bharat IndicSUPERB** - about 120 hours of speech in 12 Indian languages
- **Mozilla Common Voice** - voice recordings in Hindi, Tamil, Telugu, Bengali
- **Google FLEURS** - speech data in 10 Indian languages
- **AI4Bharat Shrutilipi** - over 6,400 hours of Indian speech (best resource)

### Module 2 - Documents (reading invoices and contracts)
- **Synthetic data** - computer-generated fake invoices and contracts (for quick testing)
- **Real data** - MSME Samadhan portal, legal document datasets, IIT-Bombay Legal NLP corpus

### Module 3 - Outcome prediction (guessing settlement results)
- **RTI request** - request real MSEFC case data from the Ministry of MSME (costs Rs.10, takes ~30 days)
- **Synthetic data** - 5,000 computer-generated cases to start training immediately

### Module 4 - Negotiation AI (learning how to mediate)
- **Sentiment datasets** - GoEmotions, EmoBank (teach AI to detect anger, frustration, etc.)
- **Bargaining dialogues** - CraigslistBargain, DealOrNoDeal (teach AI how people negotiate)
- **LLM fine-tuning** - 500 real MSEFC negotiation dialogues used to train the mediator model

### Module 5 - Settlement generation (writing legal agreements)
- **Legal templates** - MSME Samadhan settlement orders, Indian Contract Act
- **Fine-tuning** - train AI to turn case details into a proper legal agreement text

### Which data to get first?
| Module | Start now? | Need special permission? |
|---|---|---|
| M1 Voice | Yes | No |
| M2 Documents | Yes (use synthetic first) | No |
| M3 Prediction | Yes (use synthetic first) | Yes (real MSEFC data needs RTI) |
| M4 Negotiation | Yes | No (collect 500 dialogues) |
| M5 Settlement | Yes (use templates) | Yes (real MSEFC orders need permission) |


## 11. Project Structure (where everything lives)

```text
MSME Major project/
├── agriai/                 <- Python package holding AI modules
├── AIML/                   <- Phase 1 AI/ML modules (voice, documents, prediction, negotiation, settlement)
├── api/                    <- FastAPI backend (routes, auth, database models)
├── frontend/               <- React 18 web frontend (website users see in a browser)
├── Kotlin/                 <- Android app (Jetpack Compose + Retrofit)
├── data/                   <- Local datasets and vector database
├── models/                 <- Trained ML model files (stored locally)
├── uploads/                <- Uploaded audio and documents (auto-deleted after use)
├── docs/                   <- Extra documentation (deployment guides, audit reports)
├── scripts/                <- Developer utility scripts
├── tests/                  <- Pytest test suite
├── research_Paper/         <- Research papers referenced during the project
├── main.py                 <- Phase 2 demo entry point
├── requirements*.txt       <- Python dependency files
├── Dockerfile              <- Instructions to build a Docker image
└── railway.toml            <- Railway platform deployment config
```

> **Quick guide:**
> - `aiML/` = the AI brains
> - `api/` = the server that connects everything
> - `frontend/` = the website
> - `Kotlin/` = the Android mobile app
> - `data/` = where case files and datasets are stored

---

## 12. Setup & Installation (step by step)

### What you need first
| Tool | What it is for |
|---|---|
| Python 3.10+ | Runs the backend and AI modules |
| SQLite | Built-in database for development (no install needed) |
| Tesseract OCR | Reads text from images and PDFs (Windows: `choco install tesseract`) |
| Node.js 20+ | Runs the web frontend |

### Step 1: Set up the backend (FastAPI)
```bash
# Create a virtual environment (keeps project packages separate)
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Or on Linux/Mac:
# source venv/bin/activate

# Install all required Python packages
pip install -r requirements.txt

# Copy the example environment file
copy .env.example .env         # Windows
# cp .env.example .env         # Linux/Mac

# Open .env and add your database URL, JWT secret, and API keys
```

### Step 2: Run the AI modules (Phase 1)
Each module can be run on its own:
```bash
python voice_pipeline.py           # Transcribes audio and extracts names/dates
python document_intelligence.py    # Reads and classifies uploaded documents
python outcome_prediction.py       # Predicts settlement range and probability
python negotiation_ai.py           # AI mediator for negotiation chats
python settlement_generator.py     # Creates the final settlement PDF
```

### Step 3: Start the FastAPI backend
```bash
cd api
uvicorn main:app --reload --port 8000
# Open http://localhost:8000/docs in your browser to see all API routes
```

> **Tip:** Always activate the virtual environment (`venv\Scripts\activate` on Windows) before running any Python command.


## 13. API Reference (how the app talks to the server)

An **API endpoint** is like a web address that the app calls to do something — for example, create a case, log in, or upload a document.

### Base URL
**http://localhost:8000** — this is the address where the backend runs on your computer.
(In production, this is set by `api/config.py` reading the `.env` file.)

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Register a user (claimant/respondent/admin) |
| POST | `/api/auth/login` | JWT login (returns `access_token`) |
| GET | `/api/auth/profile` | Current user profile (requires Bearer token) |

### Cases
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/cases` | Create a case |
| GET | `/api/cases` | List all cases |
| GET | `/api/cases/{id}` | Get full case detail |
| PATCH | `/api/cases/{id}/status` | Update case status |
| PATCH | `/api/cases/{id}/description` | Update description (e.g. from voice dictation) |

### Documents
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/cases/{id}/documents` | Upload document(s); extracts text, classifies type |

### Voice
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/cases/{id}/voice` | Upload audio; transcribes + NER + pre-fills case fields |

### Prediction
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/cases/{id}/predict` | Run outcome prediction (settlement range + probability) |

### Negotiation (WebSocket)
| Endpoint | Description |
|---|---|
| `WS /ws/{case_id}?party=claimant|respondent` | Real-time negotiation channel |

### Settlement
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/cases/{id}/settlement` | Generate legally binding settlement PDF |
| GET | `/api/cases/{id}/settlement` | Fetch existing settlement/agreement |

### Report
| Method | Endpoint | Description |
|---|---|---|
| Various | `/api/reports/*` | Reporting endpoints |


## 14. Legal Foundation

| Legal Instrument | Role in Platform |
|---|---|
| **MSMED Act 2006** (Sections 15-23) | Core statute for payment delay liability, MSEFC process, compound interest (Section 16) |
| **Indian Contract Act 1872** | Governs validity of settlement agreements generated by Module 5 |
| **MSEFC Case Precedents** (500+) | Training data for outcome prediction and RAG legal advice |
| **Arbitration & Conciliation Act 1996** | Framework for what makes an out-of-court settlement legally binding |

> **Disclaimer:** NegotiateAI provides AI-assisted legal information grounded in statutory law and case precedents. It does NOT constitute formal legal advice. Parties are encouraged to have final settlement documents reviewed by a qualified advocate.

---

## 15. How to Run

### Backend (FastAPI)
```bash
uvicorn api.main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### Web Frontend (React 18)
```bash
cd frontend && npm start   # http://localhost:3000
```

### Demo smoke test
```bash
python demo_phase2.py
```

### Android app
```bash
cd Kotlin
gradlew :app:assembleDebug  # or ./gradlew :app:assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

### Docker
```bash
docker build -t negotiateai .
docker run -p 8000:8000 --env-file .env negotiateai
```

> **First-run flow:** Start backend -> Run app on emulator -> Register user -> Dashboard -> Create case -> **Predict** (~30-60s, trains model) -> **Negotiate** (real-time chat) -> reach agreement -> **Settle** (generates agreement).
## 16. Troubleshooting

| Problem | Fix |
| --- | --- |
| Voice upload returns a demo transcript | `GROQ_API_KEY` missing/expired - add a valid key from https://console.groq.com |
| First negotiation reply takes minutes | Local model (Qwen/Qwen2.5-1.5B-Instruct) loading - one-time per server start; or set `USE_LOCAL_MODEL=false` for fast rule-based mediator |
| App can't reach the backend | Emulator: run backend with `--host 0.0.0.0`. Physical device: change base URL to your LAN IP |
| Gradle build fails on "not a regular file" | Project lives under OneDrive - copy the `Kotlin/` folder to a normal path |
| `git status` doesn't show the app's `data/` package | It was gitignored before - run `git add Kotlin/app/src/main/java/com/negotiateai/app/data/` |

---

## 17. Key File Reference (Quick Lookup)

| Concept | File |
| --- | --- |
| Backend entry point | `api/main.py` |
| Environment / settings | `api/config.py` |
| DB engine + session | `api/database.py` |
| JWT auth | `api/auth.py` |
| User model | `api/models/user.py` |
| Case model | `api/models/case.py` |
| Case CRUD | `api/routes/cases.py` |
| Voice upload | `api/routes/voice_groq.py` |
| Outcome predictor | `AIML/outcome_prediction.py` |
| Negotiation mediator | `AIML/negotiation_ai.py` |
| Settlement PDF | `AIML/settlement_generator.py` |
| Voice ASR + NER | `AIML/voice_pipeline.py` |
| Document intelligence | `AIML/document_intelligence.py` |
| Legal RAG | `AIML/legal_rag.py` |
| Fine-tuning | `AIML/fine_tune_negotiator.py` |
| Web frontend API client | `frontend/src/api.js` |
| Android API client | `Kotlin/data/api/ApiService.kt` |
