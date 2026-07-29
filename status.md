# NegotiateAI (MSME Major Project) - Current Status and Gap Analysis

## 1. Project Overview & Current State
The project is "NegotiateAI", an Online Dispute Resolution (ODR) platform specifically designed for MSME payment disputes under the MSMED Act 2006. 

The core ML/AI architecture is cleanly divided into 5 distinct modules, all of which have functional prototype code:

*   **Module 1: Multilingual Voice Pipeline (`voice_pipeline.py`)** 
    *   **What it does**: Ingests audio, transcribes it using Whisper, translates non-English languages, extracts named entities (NER) like claimant, respondent, invoice amount, and dispute type to auto-populate forms.
*   **Module 2: Document Intelligence (`document_intelligence.py`)**
    *   **What it does**: Performs OCR on uploaded documents/PDFs, uses DistilBERT to classify document types (invoices, POs, contracts), checks for missing documents (Gap Analysis), and summarises the case.
*   **Module 3: Outcome Prediction (`outcome_prediction.py`)**
    *   **What it does**: Uses XGBoost and LightGBM models to predict the probability of an out-of-court settlement, the expected settlement amount range, and adjudication timeline. Uses SHAP values for explainability.
*   **Module 4: Negotiation AI (`negotiation_ai.py`)**
    *   **What it does**: Acts as a real-time negotiation moderator. It combines sentiment analysis (RoBERTa), game-theoretic bargaining strategy (Nash Bargaining Solution & Rubinstein Alternating Offers), and an LLM to generate neutral, context-aware mediator responses.
*   **Module 5: Settlement Generator (`settlement_generator.py`)**
    *   **What it does**: Auto-generates a legally valid settlement agreement once an agreement is reached. Uses templates grounded in the MSMED Act and can be enhanced by an LLM for complex scenarios. It includes a rule-based legal validator to ensure all mandatory clauses exist.

## 2. Updated Completion Status (Demo Scope)

For presentation and evaluation, Phase 2 backend has been completed in a demo-ready form:

### A. Backend Integration & API Layer
*   **Completed API Layer**: FastAPI routes are available for authentication, cases, documents, voice intake, prediction, negotiation, and settlement generation.
*   **Module Wiring**: Endpoints invoke the corresponding Phase 1 modules with graceful fallback behavior when heavy ML dependencies are unavailable.

### B. Database & State Management
*   **Database Models Implemented**: SQLAlchemy models exist for `User`, `Case`, `Document`, and `Message`.
*   **Persistence Enabled**: SQLite-backed persistence works out-of-the-box for local demonstration.

### C. Demonstration Proof
*   **One-command proof flow**: `demo_phase2.py` executes an end-to-end API smoke scenario:
    * register/login users
    * create case
    * run prediction
    * send negotiation message
    * generate settlement

## 3. What Still Remains (Beyond Phase 2)

The next major gaps now belong to Phase 3/4 production features:

### A. Backend Integration & API Layer
*   **Missing API**: The modules are currently standalone scripts meant for testing in terminal. You lack a web backend (like FastAPI or Flask) to expose these modules as API endpoints (e.g., `/api/upload-audio`, `/api/predict-outcome`, `/api/negotiate/message`).
*   **Orchestration**: There is no central orchestrator to pass data between modules (e.g., passing the output of Module 1 & 2 as the input state for Module 3 and 4).

### B. Database & State Management
*   **Missing Database Implementation**: Although `requirements.txt` includes `sqlalchemy`, `asyncpg`, and `alembic`, there are no database models (`models.py`), connection scripts, or migrations.
*   **State Persistence**: The `NegotiationState` in Module 4 is currently managed in-memory via Python dataclasses. This needs to be persisted to a database (like PostgreSQL) to support long-running, asynchronous negotiations between users.

### C. Frontend / User Interface
*   **Missing Web App**: There is no frontend application (e.g., React, Vue, Next.js) for users to interact with the system. You need UIs for:
    *   **Dashboard**: To view case status and predicted outcomes.
    *   **Form Upload**: UI for voice recording/uploading and document uploading.
    *   **Chat Interface**: A real-time chat UI for the negotiation phase (Module 4) where claimant, respondent, and the AI Mediator interact.

### D. Authentication & Security
*   **User Management**: No system exists for users to register, log in, or manage their profiles.
*   **Role-based Access Control (RBAC)**: The system needs to distinguish and enforce permissions between Claimants, Respondents, and System Admins.

### E. Real Data & Fine-Tuning
*   **Data Acquisition**: As noted in `DATA_SOURCES.md`, the platform heavily relies on synthetic data or base models right now. You still need to execute the RTI requests to get actual MSME Samadhan data.
*   **Model Fine-Tuning**: Many components (like the Whisper ASR, BERT Classifier, and LLM Moderator) are using fallback heuristics or generic models. They need to be formally fine-tuned on the Indian legal datasets mentioned in your documentation.

## 4. Recommended Next Steps
1.  **Phase 3 (WebSockets + Redis)**: Replace in-memory chat session storage with Redis and add true live bi-directional channels.
2.  **Phase 4 (Frontend)**: Build React UI for filing, dashboard, negotiation room, and settlement preview.
3.  **Production Hardening**: Add Alembic migrations, stricter RBAC, and environment-specific configuration.
