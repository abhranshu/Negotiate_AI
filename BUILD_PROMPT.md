# NegotiateAI — Cursor Build Instructions
> Paste this entire file into Cursor AI and say: "Build this project exactly as described."

---

## PROJECT OVERVIEW

Build a full-stack AI-powered legal negotiation assistant for Indian MSME payment disputes.
The core product is a **Generative AI that watches a live negotiation session between two parties
and gives real-time private legal suggestions to each party** based on Indian law (MSMED Act 2006,
Indian Contract Act 1872) and past MSEFC case precedents.

This is NOT a chatbot. This is a real-time AI legal co-pilot that:
- Reads the uploaded case documents (invoices, contracts, POs)
- Has a RAG pipeline over Indian legal text and past case precedents
- Watches both parties negotiate via WebSocket in real time
- Sends PRIVATE suggestions to each party separately
- Detects deadlock, ZOPA, sentiment shifts, and inconsistencies
- Drafts a legally valid settlement agreement when agreement is reached

---

## TECH STACK

```
Backend         : Python 3.11, FastAPI, WebSockets
RAG Pipeline    : LlamaIndex, ChromaDB
LLM             : Mistral 7B via Ollama (local dev) / Claude API (production)
Embeddings      : sentence-transformers (all-MiniLM-L6-v2) or InLegalBert
Sentiment       : cardiffnlp/twitter-roberta-base-sentiment (HuggingFace)
Outcome Model   : XGBoost + LightGBM (scikit-learn pipeline)
Database        : PostgreSQL (via SQLAlchemy async) + Redis (conversation state)
Frontend        : React 18, TypeScript, TailwindCSS, Vite
Real-time       : Native WebSocket API (frontend) + FastAPI WebSocket (backend)
Auth            : JWT (python-jose) + bcrypt
PDF Generation  : ReportLab
File Storage    : Local filesystem (dev) / AWS S3 compatible (prod)
```

---

## PROJECT FOLDER STRUCTURE

Create exactly this structure:

```
negotiateai/
├── backend/
│   ├── main.py                          # FastAPI app entry point
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic/                         # DB migrations
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py                    # All env vars and settings
│   │   ├── database.py                  # SQLAlchemy async engine + session
│   │   ├── redis_client.py              # Redis connection
│   │   │
│   │   ├── models/                      # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── case.py
│   │   │   ├── document.py
│   │   │   ├── negotiation.py
│   │   │   └── settlement.py
│   │   │
│   │   ├── schemas/                     # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── case.py
│   │   │   ├── negotiation.py
│   │   │   └── settlement.py
│   │   │
│   │   ├── routers/                     # FastAPI route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                  # /auth/register, /auth/login, /auth/refresh
│   │   │   ├── cases.py                 # /cases CRUD
│   │   │   ├── documents.py             # /documents/upload, /documents/analyse
│   │   │   ├── negotiation.py           # /negotiation/start, /negotiation/{id}
│   │   │   ├── prediction.py            # /prediction/analyse
│   │   │   ├── settlement.py            # /settlement/generate, /settlement/download
│   │   │   └── websocket.py             # /ws/negotiation/{session_id}
│   │   │
│   │   ├── services/                    # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── case_service.py
│   │   │   ├── document_service.py
│   │   │   ├── rag_service.py           # RAG pipeline (CORE)
│   │   │   ├── negotiation_service.py   # WebSocket + AI watcher (CORE)
│   │   │   ├── prediction_service.py    # XGBoost outcome prediction
│   │   │   ├── sentiment_service.py     # RoBERTa sentiment analysis
│   │   │   ├── settlement_service.py    # Legal doc generation
│   │   │   └── llm_service.py           # LLM abstraction layer
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── pdf_extractor.py         # PDF → clean text
│   │       ├── chunker.py               # Text chunking for RAG
│   │       ├── legal_validator.py       # Settlement doc validation
│   │       └── number_utils.py          # INR formatting helpers
│   │
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       │
│       ├── components/
│       │   ├── ui/                      # Reusable base components
│       │   │   ├── Button.tsx
│       │   │   ├── Card.tsx
│       │   │   ├── Badge.tsx
│       │   │   ├── Input.tsx
│       │   │   ├── Modal.tsx
│       │   │   ├── Spinner.tsx
│       │   │   ├── Toast.tsx
│       │   │   └── ProgressBar.tsx
│       │   │
│       │   ├── layout/
│       │   │   ├── Navbar.tsx
│       │   │   ├── Sidebar.tsx
│       │   │   ├── DashboardLayout.tsx
│       │   │   └── AuthLayout.tsx
│       │   │
│       │   ├── negotiation/
│       │   │   ├── NegotiationRoom.tsx  # Main 3-panel negotiation UI
│       │   │   ├── ChatPanel.tsx        # Center: live message thread
│       │   │   ├── CasePanel.tsx        # Left: case details + offers
│       │   │   ├── IntelligencePanel.tsx# Right: AI suggestions + sentiment
│       │   │   ├── MessageBubble.tsx
│       │   │   ├── AIsuggestionCard.tsx
│       │   │   ├── SentimentGauge.tsx
│       │   │   ├── OfferTimeline.tsx
│       │   │   └── ZOPAIndicator.tsx
│       │   │
│       │   ├── dashboard/
│       │   │   ├── KPICard.tsx
│       │   │   ├── CasesTable.tsx
│       │   │   ├── PredictionWidget.tsx
│       │   │   └── DeadlineList.tsx
│       │   │
│       │   ├── filing/
│       │   │   ├── FilingWizard.tsx     # Multi-step dispute filing
│       │   │   ├── StepVoiceInput.tsx
│       │   │   ├── StepDocuments.tsx
│       │   │   ├── StepReview.tsx
│       │   │   └── StepperBar.tsx
│       │   │
│       │   └── settlement/
│       │       ├── AgreementPreview.tsx
│       │       └── SignatureBlock.tsx
│       │
│       ├── pages/
│       │   ├── Landing.tsx
│       │   ├── Login.tsx
│       │   ├── Register.tsx
│       │   ├── Dashboard.tsx
│       │   ├── FilingPage.tsx
│       │   ├── NegotiationPage.tsx
│       │   ├── SettlementPage.tsx
│       │   └── CaseDetail.tsx
│       │
│       ├── hooks/
│       │   ├── useWebSocket.ts          # WebSocket connection manager
│       │   ├── useNegotiation.ts        # Negotiation state
│       │   ├── useAuth.ts
│       │   └── useCases.ts
│       │
│       ├── store/
│       │   ├── authStore.ts             # Zustand auth state
│       │   ├── negotiationStore.ts      # Live negotiation state
│       │   └── caseStore.ts
│       │
│       ├── api/
│       │   ├── client.ts                # Axios instance with interceptors
│       │   ├── auth.ts
│       │   ├── cases.ts
│       │   ├── documents.ts
│       │   ├── negotiation.ts
│       │   └── settlement.ts
│       │
│       └── types/
│           ├── case.ts
│           ├── negotiation.ts
│           ├── user.ts
│           └── settlement.ts
│
├── rag_data/                            # Knowledge base documents
│   ├── laws/                            # MSMED Act, Contract Act PDFs
│   ├── cases/                           # MSEFC case precedents
│   ├── tactics/                         # Negotiation frameworks
│   └── chroma_db/                       # ChromaDB vector store (generated)
│
├── ml_models/                           # Trained model files
│   ├── settlement_classifier.pkl
│   ├── settlement_pct_regressor.pkl
│   └── adjudication_days_regressor.pkl
│
├── scripts/
│   ├── ingest_documents.py              # One-time RAG document ingestion
│   ├── train_outcome_model.py           # Train XGBoost models
│   └── generate_synthetic_data.py       # Generate training data
│
└── docker-compose.yml                   # PostgreSQL + Redis + app
```

---

## BACKEND — DETAILED IMPLEMENTATION

### `backend/requirements.txt`

```txt
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
pydantic>=2.6.0
pydantic-settings>=2.2.0
python-multipart>=0.0.9
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
sqlalchemy>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0
redis>=5.0.0
aiofiles>=23.2.1

# RAG
llama-index>=0.10.0
llama-index-vector-stores-chroma>=0.1.0
llama-index-embeddings-huggingface>=0.2.0
chromadb>=0.4.0
sentence-transformers>=2.5.0

# ML
xgboost>=2.0.0
lightgbm>=4.3.0
scikit-learn>=1.4.0
shap>=0.44.0
pandas>=2.1.0
numpy>=1.26.0

# NLP / Sentiment
transformers>=4.40.0
torch>=2.1.0
spacy>=3.7.0

# LLM
httpx>=0.27.0
ollama>=0.1.0

# Documents
pytesseract>=0.3.10
Pillow>=10.0.0
pdf2image>=1.17.0
pypdf>=4.0.0
reportlab>=4.1.0
faker>=24.0.0

python-dotenv>=1.0.0
joblib>=1.3.0
```

---

### `backend/app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/negotiateai"
    REDIS_URL: str = "redis://localhost:6379"

    # Auth
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # LLM
    LLM_PROVIDER: str = "ollama"          # "ollama" or "anthropic"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"
    ANTHROPIC_API_KEY: str = ""

    # RAG
    CHROMA_DB_PATH: str = "./rag_data/chroma_db"
    RAG_DATA_PATH: str = "./rag_data"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RAG_TOP_K: int = 5
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100

    # File upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10

    class Config:
        env_file = ".env"

settings = Settings()
```

---

### `backend/app/services/rag_service.py`

Build this service with the following exact functionality:

```python
"""
RAG Service — Legal Knowledge Base
===================================
Manages two types of collections in ChromaDB:

1. GLOBAL collection ("legal_knowledge"):
   - MSMED Act 2006 full text
   - Indian Contract Act 1872
   - Arbitration and Conciliation Act 1996
   - 500+ MSEFC case precedents from Indian Kanoon
   - Negotiation tactics library
   - Ingested ONCE via scripts/ingest_documents.py

2. CASE-SPECIFIC collection ("case_{case_id}"):
   - Uploaded invoices, POs, contracts for this specific case
   - Created fresh per case when documents are uploaded
   - Enables case-specific legal advice

RETRIEVAL LOGIC:
When the AI needs context for a negotiation message:
  1. Search case-specific collection first (top 3 chunks)
  2. Search global legal collection (top 3 chunks)
  3. Combine 6 chunks as context for LLM prompt
  4. Include metadata: source document, section, relevance score
"""

class RAGService:

    def __init__(self):
        # Initialize ChromaDB client
        # Initialize HuggingFace embedding model
        # Load or create global legal collection
        pass

    async def ingest_legal_documents(self, documents_dir: str):
        """
        Ingest all PDFs from rag_data/ into global ChromaDB collection.
        Called once via scripts/ingest_documents.py
        Steps:
        1. Walk directory, find all PDFs
        2. Extract text with pypdf
        3. Clean text (remove headers/footers/page numbers)
        4. Chunk with 600-word chunks, 100-word overlap
        5. Add metadata: source_file, chunk_index, document_type (law/case/tactics)
        6. Embed and store in ChromaDB global collection
        """
        pass

    async def ingest_case_documents(self, case_id: str, file_paths: list[str]):
        """
        Ingest case-specific uploaded documents.
        Creates or updates collection named f"case_{case_id}"
        Same chunking/embedding process as above
        Called automatically when user uploads documents in filing flow
        """
        pass

    async def query(self, query_text: str, case_id: str = None, top_k: int = 5) -> list[dict]:
        """
        Retrieve relevant chunks for a query.
        If case_id provided: search both case collection AND global collection
        Returns list of: {text, source, relevance_score, chunk_type}
        """
        pass

    async def get_legal_context(self, negotiation_message: str, case_id: str) -> str:
        """
        Main method called by negotiation service.
        Takes latest message + case_id
        Returns formatted context string ready to inject into LLM prompt
        Format:
          [CASE DOCUMENTS]
          {relevant case doc chunks}

          [LEGAL PROVISIONS]
          {relevant law chunks}

          [PRECEDENTS]
          {relevant past case chunks}
        """
        pass
```

---

### `backend/app/services/negotiation_service.py`

This is the CORE service. Build it with this exact logic:

```python
"""
Negotiation Service — Real-Time AI Watcher
==========================================
Manages live negotiation sessions via WebSocket.

SESSION ARCHITECTURE:
Each session has:
  - session_id (UUID)
  - Two WebSocket connections: claimant_ws, respondent_ws
  - Redis key: "session:{session_id}" storing full conversation history
  - Separate Redis keys: "suggestion:{session_id}:claimant" and ":respondent"

MESSAGE FLOW (what happens every time a party sends a message):
  1. Message received via WebSocket
  2. Broadcast to OTHER party (they see what was said)
  3. Run sentiment analysis on the message (RoBERTa)
  4. Run pattern analysis (deadlock/ZOPA/inconsistency detection)
  5. Build LLM prompt with: system prompt + RAG context + conversation history + analysis
  6. Generate private suggestion for the SENDING party
  7. Push suggestion back to ONLY the sending party via their WebSocket channel
  8. Store everything in Redis

PRIVATE SUGGESTION LOGIC:
  - Claimant sends message → AI sends private suggestion ONLY to claimant
  - Respondent sends message → AI sends private suggestion ONLY to respondent
  - Neither party sees the other's AI suggestions
  - AI Mediator messages (visible to both) only sent during deadlock or agreement

SYSTEM PROMPT TEMPLATE:
You are a private legal AI advisor for Indian MSME payment disputes.
You are advising {party_role} in a negotiation about {dispute_type}.
Your client's claim is ₹{claim_amount}.
The predicted settlement range based on similar MSEFC cases is ₹{range_low}–₹{range_high}.

RELEVANT LEGAL CONTEXT:
{rag_context}

CONVERSATION SO FAR:
{conversation_history}

LATEST MESSAGE FROM {other_party}:
{latest_message}

ANALYSIS:
- Sentiment detected: {sentiment}
- Deadlock streak: {deadlock_count} rounds
- ZOPA status: {zopa_status}
- Inconsistencies detected: {inconsistencies}

Give your client a private suggestion (2-3 sentences max):
1. What this message means strategically
2. What they should say next (suggest exact wording if helpful)
3. Legal basis if relevant (cite MSMED Act section)

Be direct, practical, and brief. This is private advice — speak like a lawyer to their client.
"""

class NegotiationService:

    def __init__(self, rag_service, llm_service, sentiment_service):
        # active_sessions: dict[session_id, SessionState]
        # Each SessionState holds: claimant_ws, respondent_ws, case_id, history, offer_history
        pass

    async def create_session(self, case_id: str, claimant_id: str, respondent_id: str) -> str:
        """Create new session, return session_id"""
        pass

    async def connect(self, websocket, session_id: str, party: str, user_id: str):
        """
        Handle WebSocket connection for a party.
        party: "claimant" or "respondent"
        Store websocket reference in session state
        Send welcome message with case context to connecting party
        """
        pass

    async def handle_message(self, session_id: str, party: str, message: dict):
        """
        Core message handler. Called for every message received.
        message dict: {type: "chat"|"offer"|"system", text: str, offer_amount: float|None}

        Steps:
        1. Store message in Redis conversation history
        2. Broadcast message to other party
        3. Run analysis (sentiment, ZOPA, deadlock, inconsistency)
        4. Build LLM prompt with RAG context
        5. Generate private suggestion
        6. Send suggestion to sending party only
        7. Check if mediator intervention needed (deadlock/agreement)
        """
        pass

    async def _detect_patterns(self, session_id: str, latest_message: dict) -> dict:
        """
        Pattern analysis engine. Returns:
        {
          sentiment: str,
          deadlock: bool,
          deadlock_streak: int,
          zopa_reached: bool,
          zopa_amount: float | None,
          inconsistencies: list[str],
          suggested_mediator_move: str | None
        }

        DEADLOCK: if last 3 messages had no offer movement AND sentiment is frustrated/hostile
        ZOPA: if claimant_last_offer <= respondent_last_offer
        INCONSISTENCY: compare what parties say against their uploaded documents
          e.g. respondent claims "goods were defective" but delivery receipt shows "accepted"
        """
        pass

    async def _generate_private_suggestion(
        self, session_id: str, party: str, analysis: dict
    ) -> str:
        """
        Build full prompt and call LLM.
        Inject RAG context from rag_service.get_legal_context()
        Return suggestion text
        """
        pass

    async def _handle_agreement(self, session_id: str, agreed_amount: float):
        """
        Called when ZOPA is detected and parties confirm agreement.
        Trigger settlement generation.
        Broadcast agreement notification to both parties.
        """
        pass

    async def disconnect(self, session_id: str, party: str):
        """Handle WebSocket disconnect gracefully"""
        pass
```

---

### `backend/app/services/sentiment_service.py`

```python
"""
Sentiment Service
=================
Uses cardiffnlp/twitter-roberta-base-sentiment from HuggingFace.
No fine-tuning needed — use out of the box.

Labels mapped to negotiation context:
  LABEL_2 (positive) → "cooperative" or "conciliatory"
  LABEL_1 (neutral)  → "neutral"
  LABEL_0 (negative) → "frustrated" (moderate score) or "hostile" (high score)

Additional keyword boost layer:
  If "refuse", "fraud", "lawsuit", "unacceptable" present → boost toward "hostile"
  If "understand", "willing", "compromise" present → boost toward "conciliatory"
"""

class SentimentService:

    def __init__(self):
        # Load cardiffnlp/twitter-roberta-base-sentiment pipeline
        # Use device=0 if CUDA available, else -1
        pass

    def analyse(self, text: str) -> dict:
        """
        Returns:
        {
          label: "cooperative" | "neutral" | "frustrated" | "hostile" | "conciliatory",
          score: float,
          raw_label: str
        }
        """
        pass

    def analyse_conversation_trend(self, messages: list[str]) -> dict:
        """
        Analyse trend across last N messages.
        Returns:
        {
          overall_trend: "improving" | "stable" | "deteriorating",
          hostile_count: int,
          cooperative_count: int,
          deadlock_signal: bool
        }
        """
        pass
```

---

### `backend/app/services/llm_service.py`

```python
"""
LLM Service — Abstraction Layer
================================
Supports two providers:
  1. Ollama (local, free) — for development
     Model: mistral or llama3
     Endpoint: http://localhost:11434/api/generate

  2. Anthropic Claude API — for production
     Model: claude-sonnet-4-20250514
     Endpoint: https://api.anthropic.com/v1/messages

Switch via LLM_PROVIDER env variable.
"""

class LLMService:

    def __init__(self, provider: str, model: str, api_key: str = None):
        pass

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 300,
        temperature: float = 0.3       # Low temp for consistent legal advice
    ) -> str:
        """
        Generate text from LLM.
        Handles both Ollama and Anthropic seamlessly.
        Returns clean text response.
        """
        pass

    async def generate_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Retry wrapper with exponential backoff"""
        pass
```

---

### `backend/app/services/prediction_service.py`

```python
"""
Outcome Prediction Service
==========================
XGBoost classifier for settlement probability.
LightGBM regressor for settlement amount range and adjudication days.

Features used (18 total):
  claim_amount_inr, amount_log, overdue_days, overdue_ratio,
  previous_payments_made, invoice_count, documentation_score,
  has_signed_contract, has_delivery_proof,
  claimant_size, respondent_size, prior_disputes,
  industry, dispute_type, state, msefc_filing,
  days_since_dispute, doc_amount_interaction

Models loaded from ml_models/ directory.
If models don't exist, train them first via scripts/train_outcome_model.py
"""

class PredictionService:

    def predict(self, case_features: dict) -> dict:
        """
        Returns:
        {
          settlement_probability: float,     # 0.0 - 1.0
          settlement_range_low: float,       # INR
          settlement_range_high: float,      # INR
          adjudication_days: int,
          confidence: "high" | "medium" | "low",
          key_factors: list[dict],           # SHAP top 5
          recommendation: str
        }
        """
        pass
```

---

### `backend/app/services/settlement_service.py`

```python
"""
Settlement Document Service
============================
Generates legally valid settlement agreements using:
  1. Template system (always runs — deterministic, fast)
  2. LLM polish for non-standard clauses (optional)
  3. Rule-based legal validator before delivery

Output: PDF document via ReportLab
Required clauses validated:
  - Parties identified
  - Agreed amount present
  - Payment schedule defined
  - Full and final settlement language
  - MSMED Act reference
  - Indian Contract Act reference
  - Governing law clause
  - Signature blocks

Generated in under 60 seconds.
"""

class SettlementService:

    async def generate(self, negotiation_session_id: str) -> dict:
        """
        Pull all data from negotiation session.
        Generate agreement text from template.
        Optionally polish with LLM.
        Validate with legal checker.
        Render to PDF via ReportLab.
        Save to filesystem.
        Returns: {agreement_id, pdf_path, is_valid, validation_notes}
        """
        pass

    def validate(self, agreement_text: str, terms: dict) -> tuple[bool, list[str]]:
        """Rule-based validation. Returns (is_valid, issues_list)"""
        pass
```

---

### `backend/app/routers/websocket.py`

```python
"""
WebSocket Router
================
Endpoint: ws://localhost:8000/ws/negotiation/{session_id}?token={jwt}&party={claimant|respondent}

Message format (client → server):
{
  "type": "chat" | "offer" | "typing" | "ping",
  "text": "message text",
  "offer_amount": 320000.00    // only for type="offer"
}

Message format (server → client):
{
  "type": "message" | "suggestion" | "system" | "agreement" | "pong",
  "from": "claimant" | "respondent" | "ai_mediator" | "ai_advisor",
  "text": "message text",
  "sentiment": "neutral",
  "timestamp": "ISO8601",
  "offer_amount": null,
  "is_private": true           // true for AI suggestions (only visible to recipient)
}

AUTH: Validate JWT token from query param before accepting connection.
If token invalid, close with code 4001.
"""
```

---

### `backend/app/routers/documents.py`

```python
"""
Documents Router
================
POST /documents/upload
  - Accept multipart file upload (PDF, JPG, PNG)
  - Max 10MB per file
  - Save to uploads/{case_id}/
  - Trigger: OCR extraction, document type classification, RAG ingestion
  - Return: {document_id, detected_type, confidence, extracted_fields, missing_docs_checklist}

POST /documents/analyse/{case_id}
  - Run full document intelligence on all uploaded documents for a case
  - Return case summary with gap analysis

GET /documents/{document_id}
  - Return document metadata and extracted text
"""
```

---

### `backend/main.py`

```python
"""
FastAPI Application Entry Point
================================
Include all routers.
Add CORS middleware (allow localhost:5173 for Vite dev server).
Add JWT auth middleware.
On startup: initialize RAG service, load ML models, connect to Redis.
WebSocket endpoint registered at /ws/negotiation/{session_id}
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, cases, documents, negotiation, prediction, settlement, websocket

app = FastAPI(title="NegotiateAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,        prefix="/auth",        tags=["auth"])
app.include_router(cases.router,       prefix="/cases",       tags=["cases"])
app.include_router(documents.router,   prefix="/documents",   tags=["documents"])
app.include_router(negotiation.router, prefix="/negotiation", tags=["negotiation"])
app.include_router(prediction.router,  prefix="/prediction",  tags=["prediction"])
app.include_router(settlement.router,  prefix="/settlement",  tags=["settlement"])
app.include_router(websocket.router,   tags=["websocket"])
```

---

## FRONTEND — DETAILED IMPLEMENTATION

### Design System (TailwindCSS config)

```typescript
// tailwind.config.ts
// Extend with these custom values:
colors: {
  navy:    { DEFAULT: '#0A1628', light: '#0D1B2E', card: '#112240' },
  indigo:  { DEFAULT: '#4F46E5', light: '#6366F1', glow: 'rgba(79,70,229,0.15)' },
  emerald: { DEFAULT: '#10B981' },
  amber:   { DEFAULT: '#F59E0B' },
  coral:   { DEFAULT: '#EF4444' },
  muted:   { DEFAULT: '#94A3B8' },
}
fontFamily: {
  sans:    ['Inter', 'sans-serif'],
  display: ['Sora', 'sans-serif'],
}
borderRadius: {
  card: '12px',
  btn:  '8px',
}
```

---

### `frontend/src/hooks/useWebSocket.ts`

```typescript
/**
 * WebSocket hook — manages real-time negotiation connection
 *
 * Usage: const { sendMessage, messages, suggestions, status } = useWebSocket(sessionId, party)
 *
 * Handles:
 * - Connection with JWT auth token in query param
 * - Auto-reconnect on disconnect (exponential backoff, max 5 retries)
 * - Message parsing and routing:
 *     type="message"    → add to messages array (visible to both)
 *     type="suggestion" → add to suggestions array (private, only for this party)
 *     type="system"     → show as system notification
 *     type="agreement"  → trigger agreement modal
 * - Typing indicators (send type="typing" on input change, debounced 500ms)
 * - Ping/pong keepalive every 30 seconds
 *
 * Returns:
 * {
 *   sendMessage: (text: string, offerAmount?: number) => void
 *   sendOffer: (amount: number) => void
 *   messages: Message[]
 *   suggestions: AISuggestion[]        // private AI suggestions for this party
 *   status: "connecting"|"connected"|"disconnected"|"error"
 *   otherPartyTyping: boolean
 *   agreementReached: boolean
 *   agreedAmount: number | null
 * }
 */
```

---

### `frontend/src/components/negotiation/NegotiationRoom.tsx`

```typescript
/**
 * Main negotiation room — 3-panel layout
 *
 * Layout: CSS Grid, 3 columns: 25% | 50% | 25%
 * Background: dark navy #0A1628
 * Full viewport height, no scroll on outer container
 *
 * Left panel (CasePanel):
 *   - Dark navy #0D1B2E background
 *   - Case ID, parties, claim amount at top
 *   - Compact prediction donut chart (recharts PieChart)
 *   - "Current Offers" bidirectional bar:
 *       Single horizontal axis, claimant offer shown in indigo from left,
 *       respondent offer shown in emerald from right,
 *       gap between them highlighted in amber
 *   - Session controls: Mute button, End Session button
 *
 * Center panel (ChatPanel):
 *   - White/light background
 *   - Scrollable message list (auto-scroll to bottom on new message)
 *   - Message bubbles:
 *       Claimant: right-aligned, indigo background, white text
 *       Respondent: left-aligned, gray background, dark text
 *       AI Mediator: full-width centered banner, indigo-tinted
 *   - Each bubble: party name, timestamp, language flag emoji
 *   - Typing indicator: animated 3-dot pulse when other party is typing
 *   - Sticky input bar at bottom:
 *       Language selector (dropdown with flags) | Text input | Voice button | Send button
 *
 * Right panel (IntelligencePanel):
 *   - Dark navy background
 *   - SentimentGauge: semicircular arc meter animating smoothly
 *       Left = Hostile (red), Center = Neutral (gray), Right = Cooperative (green)
 *       Needle animates to current sentiment score
 *   - AIsuggestionCard: shows latest private AI suggestion
 *       Indigo-tinted card, "🤖 Private Advice" label
 *       Suggestion text in white
 *       Subtle pulse animation when new suggestion arrives
 *   - OfferTimeline: vertical list of all offers made
 *       Each offer: party icon + amount + timestamp + directional arrow
 *       Shows convergence visually (arrows getting closer)
 *   - ZOPAIndicator: appears when ZOPA detected
 *       Green glowing card: "Agreement Zone Reached! Suggested: ₹X"
 *       CTA button: "Confirm Agreement"
 */
```

---

### `frontend/src/components/negotiation/SentimentGauge.tsx`

```typescript
/**
 * Semicircular sentiment arc meter
 *
 * Implementation: SVG-based arc
 * - Draw a semicircle arc from 180° to 0°
 * - Color gradient: red (0%) → gray (50%) → green (100%)
 * - Needle: thin line from center to arc, rotates based on sentiment score
 * - Needle rotation: -90° (hostile) to +90° (cooperative)
 * - Animate needle with CSS transition: 800ms ease-out
 * - Labels: "Hostile" on left, "Neutral" in center, "Cooperative" on right
 * - Current label shown below center in bold colored text
 *
 * Props: { sentiment: string, score: number }
 */
```

---

### `frontend/src/components/filing/FilingWizard.tsx`

```typescript
/**
 * Multi-step dispute filing wizard
 *
 * Steps: Voice Input → Documents → AI Review → Confirm
 *
 * StepperBar: horizontal progress bar with 4 numbered circles
 *   Connected by a line. Active = indigo filled. Complete = green checkmark. Future = gray.
 *
 * Step 1 (Voice Input):
 *   - Large centered microphone button (80px, indigo, pulse glow animation when recording)
 *   - Record button toggles recording state
 *   - Below: "Or type your complaint" toggle
 *   - Language selector dropdown (12 Indian languages with native script labels)
 *   - Form fields auto-populate as NER extracts entities from API response:
 *       Fields animate slide-in with green checkmark when filled
 *       Fields: Claimant Name, Respondent Name, Invoice Amount, Due Date, Dispute Type
 *   - Missing fields highlighted in red with "Required" badge
 *
 * Step 2 (Documents):
 *   - Drag-and-drop zone: dashed indigo border, 280px height, cloud upload icon
 *   - Uploaded files list: thumbnail | filename | AI-detected type badge | remove button
 *   - Missing documents checklist below: red X for missing, green check for present
 *   - Priority labels: "Critical" in red, "Required" in amber, "Optional" in gray
 *
 * Step 3 (AI Review):
 *   - Two columns inside card
 *   - Left: structured case summary (all extracted fields in a clean list)
 *   - Right: Prediction widget
 *       Large donut chart (recharts) animates draw-in on mount
 *       Shows settlement probability %
 *       Below: "Likely Range: ₹X – ₹Y" horizontal range bar
 *       Below: "Est. Timeline if no settlement: X days" badge
 *
 * Step 4 (Confirm):
 *   - Summary of everything
 *   - "Send Dispute Notice to Respondent" button (triggers email/SMS)
 *   - "Start Negotiation Now" button → navigates to NegotiationRoom
 */
```

---

### `frontend/src/pages/Dashboard.tsx`

```typescript
/**
 * Main dashboard page (post-login)
 *
 * Layout: DashboardLayout wrapper (sidebar + main content)
 *
 * Top: Greeting "Good morning, {name} 👋" + subtitle showing pending action count
 *
 * KPI Row: 4 cards in a grid (2x2 on mobile, 4x1 on desktop)
 *   Each card: white background, 12px radius, 20px padding
 *   - Active Cases: count in indigo
 *   - Total Claimed: ₹ amount in navy
 *   - Settlements Won: count in emerald
 *   - Avg Resolution: "X days" in amber
 *   Each card has a small sparkline (recharts LineChart, no axes, just the line)
 *
 * Main Grid: 65% / 35% on desktop, stacked on mobile
 *   Left (65%): CasesTable
 *     White card with shadow
 *     Columns: Case ID | Opponent | Amount | Status | Last Activity | Action
 *     Status badge colors:
 *       "In Negotiation" → amber background
 *       "Settled"        → emerald background
 *       "Pending Docs"   → coral background
 *       "New"            → indigo background
 *     Row hover: light indigo tint
 *     Pagination: simple prev/next at bottom
 *
 *   Right (35%): Stacked cards
 *     - PredictionWidget: compact donut + settlement range for most active case
 *     - DeadlineList: upcoming filing deadlines with urgency color coding
 *     - Quick Actions: 3 icon buttons (Upload Doc, Start Negotiation, Download Settlement)
 */
```

---

## DATABASE MODELS

### Case model fields:
```
id, case_number, claimant_id, respondent_id,
claim_amount, dispute_type, industry, state,
status (enum: draft/active/negotiating/settled/arbitrating/closed),
documentation_score, settlement_amount, resolution_days,
created_at, updated_at
```

### NegotiationSession model fields:
```
id, case_id, claimant_id, respondent_id,
status (enum: waiting/active/paused/completed/abandoned),
last_claimant_offer, last_respondent_offer,
agreed_amount, rounds_count, started_at, ended_at
```

### Message model fields:
```
id, session_id, party (enum: claimant/respondent/ai_mediator/ai_advisor),
message_type (enum: chat/offer/system/suggestion),
text, offer_amount, sentiment, is_private,
recipient_party, timestamp
```

---

## SCRIPTS

### `scripts/ingest_documents.py`

```python
"""
One-time document ingestion script.
Run: python scripts/ingest_documents.py

Before running:
1. Place PDFs in rag_data/laws/     (MSMED Act, Contract Act, etc.)
2. Place PDFs in rag_data/cases/    (MSEFC case precedents)
3. Place TXTs in rag_data/tactics/  (Negotiation frameworks)

Script does:
1. Walk all three directories
2. Extract text from each PDF using pypdf
3. Clean text (remove page numbers, headers, excessive whitespace)
4. Chunk into 600-word pieces with 100-word overlap
5. Add metadata: {source_file, doc_type, chunk_index}
6. Embed using sentence-transformers
7. Store in ChromaDB collection "legal_knowledge"
8. Print summary: total documents, total chunks, time taken

Expected output: ~2000-5000 chunks for a good knowledge base
"""
```

### `scripts/train_outcome_model.py`

```python
"""
Train outcome prediction models.
Run: python scripts/train_outcome_model.py

1. Check if real MSEFC data exists in data/msefc_cases.csv
2. If not, generate 5000 synthetic cases (generate_synthetic_data.py)
3. Train XGBoost settlement classifier (AUC target: >0.75)
4. Train LightGBM settlement % regressor (MAE target: <0.08)
5. Train LightGBM adjudication days regressor
6. Save all 3 models to ml_models/ directory
7. Print evaluation metrics for each model
8. Generate SHAP summary plot saved to ml_models/shap_summary.png
"""
```

---

## DOCKER COMPOSE

```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: negotiateai
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

## ENV TEMPLATE

```env
# .env.example
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/negotiateai
REDIS_URL=redis://localhost:6379
SECRET_KEY=change-this-to-a-random-64-char-string
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
ANTHROPIC_API_KEY=
CHROMA_DB_PATH=./rag_data/chroma_db
RAG_DATA_PATH=./rag_data
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
UPLOAD_DIR=./uploads
```

---

## BUILD ORDER FOR CURSOR

Tell Cursor to build in exactly this sequence:

```
PHASE 1 — Foundation (do this first):
1. Create full folder structure
2. docker-compose.yml
3. backend/requirements.txt
4. backend/app/config.py
5. backend/app/database.py
6. backend/app/redis_client.py
7. All SQLAlchemy models (models/)
8. All Pydantic schemas (schemas/)
9. Auth router + auth service (JWT login/register)
10. backend/main.py
11. Frontend: Vite + React + Tailwind setup
12. Frontend: API client (axios), auth store (zustand), login/register pages

PHASE 2 — RAG Pipeline (do this second):
1. scripts/ingest_documents.py
2. backend/app/utils/pdf_extractor.py
3. backend/app/utils/chunker.py
4. backend/app/services/rag_service.py
5. Test: run ingest script, verify ChromaDB has chunks, test a query

PHASE 3 — ML Models (do this third):
1. scripts/generate_synthetic_data.py
2. scripts/train_outcome_model.py
3. backend/app/services/prediction_service.py
4. backend/app/routers/prediction.py
5. Test: train models, test prediction endpoint with sample case

PHASE 4 — Core AI Negotiator (do this fourth — most important):
1. backend/app/services/sentiment_service.py
2. backend/app/services/llm_service.py
3. backend/app/services/negotiation_service.py
4. backend/app/routers/websocket.py
5. frontend/src/hooks/useWebSocket.ts
6. frontend/src/components/negotiation/ (all files)
7. frontend/src/pages/NegotiationPage.tsx
8. Test: open two browser tabs, connect as claimant + respondent,
         send messages, verify AI suggestions appear privately

PHASE 5 — Document Intelligence + Filing:
1. backend/app/utils/pdf_extractor.py (OCR)
2. backend/app/services/document_service.py
3. backend/app/routers/documents.py
4. frontend/src/components/filing/ (all files)
5. frontend/src/pages/FilingPage.tsx

PHASE 6 — Settlement Generation:
1. backend/app/services/settlement_service.py
2. backend/app/routers/settlement.py
3. backend/app/utils/legal_validator.py
4. frontend/src/components/settlement/
5. frontend/src/pages/SettlementPage.tsx

PHASE 7 — Dashboard + Polish:
1. frontend/src/pages/Dashboard.tsx
2. frontend/src/components/dashboard/
3. frontend/src/pages/Landing.tsx
4. All remaining UI polish
```

---

## DATA SOURCES (for RAG knowledge base)

Collect these documents before running `scripts/ingest_documents.py`:

**Place in `rag_data/laws/`:**
- MSMED Act 2006: https://indiacode.nic.in/handle/123456789/1556
- Indian Contract Act 1872: https://indiacode.nic.in/handle/123456789/2187
- Arbitration and Conciliation Act 1996: https://indiacode.nic.in/handle/123456789/1047

**Place in `rag_data/cases/`:**
- Go to https://indiankanoon.org
- Search: "MSEFC delayed payment" → download top 100 judgements as PDF
- Search: "MSMED Act Section 18" → download top 100 judgements as PDF
- Search: "MSEFC conciliation settlement" → download top 100 judgements as PDF
- File RTI at https://rtionline.gov.in for anonymised MSEFC case summaries

**Place in `rag_data/tactics/`:**
- Create text files summarising:
  - Nash Bargaining Solution framework
  - BATNA/WATNA/ZOPA concepts
  - Principled negotiation (Harvard framework)
  - Indian commercial negotiation norms

---

## TESTING CHECKLIST

After each phase, verify:

- [ ] Phase 1: Can register, login, get JWT, make authenticated requests
- [ ] Phase 2: RAG returns relevant legal text for "delayed payment MSMED Act"
- [ ] Phase 3: Prediction endpoint returns settlement probability for sample case
- [ ] Phase 4: Two WebSocket clients can exchange messages; AI suggestion appears privately; sentiment gauge updates in real time
- [ ] Phase 5: PDF upload extracts text; document type classified correctly; missing docs checklist generated
- [ ] Phase 6: Settlement PDF generated with valid legal clauses; passes validator
- [ ] Phase 7: Dashboard loads cases, KPIs show correct data

---

## IMPORTANT NOTES FOR CURSOR

1. Use async/await throughout the FastAPI backend — no synchronous database calls
2. All WebSocket message handling must be non-blocking — use asyncio.create_task() for AI generation so it doesn't block message delivery
3. ChromaDB collections must be initialized on app startup, not per-request
4. JWT token must be validated in WebSocket handshake via query parameter (not header — browsers don't support custom headers in WebSocket)
5. Redis conversation history key format: `negotiation:{session_id}:history` — store as JSON list, max 50 messages (trim older ones)
6. Private AI suggestions must NEVER be broadcast to the other party — enforce this at the WebSocket router level
7. All monetary amounts stored as integers in paise (1 rupee = 100 paise) in database to avoid floating point errors — convert to rupees only at API response level
8. CORS must allow WebSocket connections from frontend origin
