# NegotiateAI — Change Log & Setup Guide

This document lists **every change made to the project** (in this session) and explains
**how to start and run the project** (backend + Android app + web frontend).

---

## Part 1 — All Changes Made

### 1.1 Backend (Python / FastAPI)

| File | Change |
|---|---|
| `api/routes/settlement.py` | **Rewritten.** Was a duplicate of the *documents* router (shadowed). Now the real **Module 5** endpoints: `POST /api/cases/{id}/settlement` (generates a validated MSMED-compliant agreement via `settlement_generator.py`, persists it, sets case status to `closed`) and `GET /api/cases/{id}/settlement` (fetches an existing agreement). Requires `agreement_amount` (i.e. negotiation reached a deal). |
| `api/routes/documents.py` | Removed the duplicate `POST /{case_id}/voice` route. Kept only the documents routes — this un-shadowed the **Groq Whisper voice module**. |
| `api/routes/voice_groq.py` | Returns the updated case (`CaseOut`) instead of a custom dict (matches app + web contracts). Removed unused `tempfile` import. **Graceful degradation:** any Groq failure (invalid/expired key, network) now falls back to a demo transcript instead of HTTP 500. **Voice NER results persisted:** names, due date, invoice number, language and transcript stored in the case's `doc_gap_analysis` JSON; a matched registered respondent is auto-linked. |
| `api/schemas/case.py` | Added `SettlementOut` response model for the settlement endpoints. |
| `settlement_generator.py` | Fixed the "agreed amount" validator bug (comma-formatted amounts). **Removed the Anthropic/LLM dependency** — settlement is now 100% template-based. |
| `api/routes/cases.py` | Concurrency-safe case numbering: max-based (not `count()`) + retry up to 3x on the unique-constraint race. |
| `api/routes/negotiate.py` | `_SESSIONS` cache now prunes itself: 30-min idle TTL + hard cap of 100 (was a memory leak). |
| `AIML/negotiation_ai.py` | Crash-proofed the `nash_solution` f-string — missing/`None` -> `N/A`, numeric -> `₹75,000`. |
| `api/routes/__init__.py` | Removed the import of the deleted `voice.py`. |
| `.gitignore` | Fixed a bare `data/` pattern that was ignoring the **entire Android `data` package**; anchored to root `/data/*`. |
| **Deleted:** `api/routes/voice.py` | Dead, unregistered duplicate of the voice route. |

### 1.2 Android App (Kotlin / Jetpack Compose)

| File | Change |
|---|---|
| `data/model/Models.kt` | Added `PredictionDto`, `KeyFactor`, `SettlementDto`, `WsFrame`. |
| `data/api/ApiService.kt` | Added `POST /api/cases/{id}/predict`, `POST`/`GET /api/cases/{id}/settlement`. |
| `data/repository/CaseRepository.kt` | Added `runPrediction`, `generateSettlement`, `getSettlement`, `uploadVoice`, `uploadDocuments`. |
| `core/network/NegotiationWebSocket.kt` | **Rewritten.** Fixed URL (`ws://10.0.2.2:8000/api/cases/ws/{id}?party=...`), payload (`{text, offer}`), frame parsing; added connection state. |
| `feature/negotiation/NegotiationChatScreen.kt` | Real-time WebSocket chat (REST fallback) + joins as the logged-in role (claimant/respondent). |
| `feature/prediction/PredictionScreen.kt` | Added the **"Run ML Prediction"** button — actually calls `/predict` and shows fresh results + SHAP factors. |
| `feature/settlement/SettlementScreen.kt` | Added generate/load settlement agreement UI (full text + validation). |
| `feature/case/CaseDetailScreen.kt` | Added **voice recording** and **document upload** cards. |
| `feature/auth/AuthScreen.kt` | Fixed the register **role toggle** (real Claimant/Respondent buttons). |
| `feature/dashboard/CaseDashboardScreen.kt` | Case list **refreshes on every resume** (new cases appear without logout). |
| `data/SessionManager.kt` | Added **user role persistence** (`userRole` flow + save/clear). |
| `data/repository/AuthRepository.kt` | After login, calls `GET /api/auth/me` and persists user **id + role**. |
| `navigation/AppNavigation.kt` | Clears the role on logout. |
| `app/src/main/AndroidManifest.xml` | Added `RECORD_AUDIO` permission (voice notes). |
| **Deleted:** `feature/settlement/NetworkResult.kt` | Stale duplicate of `core/network/NetworkResult.kt`. |

### 1.3 Verified End-to-End (emulator test)

Full flow tested live on the Android emulator against the real backend (Supabase DB):

1. **Register / Login** ✅ (claimant `flow.test@test.com` and respondent `resp@test.com`)
2. **Create case** ✅ (`NAI-2026-0010` — Rs 4,50,000 claim)
3. **Run prediction** ✅ — 20% probability, Rs 2,92,500–Rs 3,82,500 range, ~131 days, SHAP factors shown in-app
4. **Negotiate** ✅ — WebSocket "Live (real-time)", claimant offer Rs 3,00,000 → mediator reply over WS → respondent offer Rs 3,50,000 → **agreement at Rs 3,25,000**, status `agreement`, messages persisted
5. **Generate settlement** ✅ — agreement `NAIODR-NAI-2026-0010` generated in-app, **✓ Validated (all clauses present)**, case status → `closed`, persisted in Supabase

### 1.4b Negotiation Latency Improvements (this session)

- **Streaming replies over WebSocket** — the WS negotiation room now pushes
  `mediator_started` (metadata: sentiment/phase/round) → `mediator_token*`
  (text chunks as they are generated) → `mediator_response` (final authoritative
  frame). First tokens appear in ~100–300ms instead of after the full 30–90s
  generation; generation runs on a worker thread so the event loop stays free.
  Kotlin app + web frontend render the live bubble.
- **Smaller default model** — `LOCAL_MODEL_ID=Qwen/Qwen2.5-3B-Instruct`
  (int8-quantized on CPU via `LOCAL_MODEL_QUANTIZE=true`) replaces the 11GB
  LegalParam as the default when `USE_LOCAL_MODEL=true`. LegalParam remains
  selectable. Chat-template formatting for standard models; legacy `<user>`/
  `<assistant>` format kept for LegalParam.
- **Micro-optimizations** — sentiment analyser and TF-IDF RAG retriever are now
  process-wide singletons (were rebuilt per case); `max_new_tokens` 80 → 64;
  degenerate-stream fallback to the rule-based responder.

### 1.4 Known Issues Still Open (not yet fixed)

- **Security:** WebSocket endpoint has no authentication; `GET /api/cases/{id}/documents` has no party authorization.
- **App:** MediaRecorder isn't released when leaving the screen mid-recording.
- **Config:** the `.env` `GROQ_API_KEY` is expired (voice works in demo-stub mode until replaced).

---

## Part 2 — How to Start the Project

### 2.1 Prerequisites

- **Python 3.11+**
- **Node.js 18+** (only needed for the web frontend)
- **Android Studio / Android SDK** (compileSdk 34, minSdk 26, Java 17) — for the app
- An **emulator** (or a physical device on the same network)

### 2.2 Environment setup (`.env`)

```bash
cp .env.example .env
```

Then edit `.env`:

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | SQLite for local dev, or your Supabase/Postgres URL | `sqlite:///./phase2_demo.db` |
| `SECRET_KEY` | JWT signing secret — `python -c "import secrets; print(secrets.token_hex(32))"` | change-me |
| `USE_LOCAL_MODEL` | `true` = local LLM mediator (small model by default); `false` = fast rule-based mediator | `false` |
| `LOCAL_MODEL_ID` | HF model loaded when `USE_LOCAL_MODEL=true` (default `Qwen/Qwen2.5-3B-Instruct`; set to `bharatgenai/LegalParam` for the 11GB legal model) | `Qwen/Qwen2.5-3B-Instruct` |
| `LOCAL_MODEL_QUANTIZE` | int8-dynamic-quantize on CPU (~2–3x faster inference, ~60% less memory) | `true` |
| `GROQ_API_KEY` | Voice transcription (Whisper-large-v3). **Current key is expired — replace it** | empty |


> ⚠️ **Local model requirements:** the default Qwen2.5-3B-Instruct downloads once (~2–6GB) on first load and is int8-quantized on CPU (~5–15s per reply) or loaded fp16 on a GPU (~1–2s). The legacy `bharatgenai/LegalParam` needs ~11GB RAM and `transformers<5` (project pins `transformers>=4.40.0,<5`).

### 2.3 Backend (FastAPI)

```bash
# 1. Create/activate a virtual env and install dependencies
python -m venv .venv
# Windows:
.venv/Scripts/activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements_deploy.txt

# 2. (Optional) Build the legal RAG index — add MSMED Act / Contract Act
#    text files to data/legal/ first, then:
python -m AIML.legal_rag --build

# 3. Start the server (Windows console needs UTF-8 for the log emoji)
PYTHONUTF8=1 uvicorn api.main:app --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 2.4 Android App

```bash
# Build & install (from the Kotlin/ directory)
cd Kotlin
./gradlew :app:assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Or open the `Kotlin/` folder in Android Studio and press **Run**.

**Backend URL:** the app points at `http://10.0.2.2:8000` (emulator loopback to your machine).
- **Emulator** → works as-is.
- **Physical device** → change `BASE_URL` in `core/network/ApiClient.kt` (and the `ws://` URL in `core/network/NegotiationWebSocket.kt`) to your machine's LAN IP, e.g. `http://192.168.1.10:8000`; phone and PC must be on the same network.

> 🪟 **Windows / OneDrive note:** if the project lives under OneDrive (e.g. `C:\Users\You\OneDrive\Desktop\...`), Gradle file-snapshotting fails with *"not a regular file"*. Copy the `Kotlin/` folder to a normal path (e.g. `C:\dev\naiapp`) before building.

### 2.5 Web Frontend (optional)

```bash
cd frontend
npm install
npm start        # http://localhost:3000
npm run build    # production build
```

The frontend's API base URL is configured in `frontend/src/api.js` (or `frontend/.env`).

### 2.6 Docker (deployment)

```bash
docker build -t negotiateai .
docker run -p 8000:8000 --env-file .env negotiateai
```

> Note: the Docker image installs **CPU-only** torch and does **not** bundle the 11GB model — keep `USE_LOCAL_MODEL=false` (default) on the deployed server, or the model downloads at first use (needs ~11GB RAM).

### 2.7 First-run flow (to verify everything works)

1. Start the backend (section 2.3).
2. Run the app on the emulator (section 2.4).
3. Register a user → dashboard.
4. Create a case → **Predict** (first run trains the model, ~30–60s) → **Negotiate** (real-time chat) → reach an agreement → **Settle** (generates the legal agreement).
5. Every step is verified working (see section 1.3).

### 2.8 Troubleshooting

| Problem | Fix |
|---|---|
| Voice upload returns a demo transcript | `GROQ_API_KEY` missing/expired — add a valid key from https://console.groq.com |
| First negotiation reply takes minutes | That's the 11GB LegalParam loading — one-time per server start; or set `USE_LOCAL_MODEL=false` for the fast rule-based mediator |
| App can't reach the backend | Emulator: run backend with `--host 0.0.0.0`. Physical device: change base URL to your LAN IP (section 2.4) |
| Gradle build fails on "not a regular file" | Project is under OneDrive — copy the `Kotlin/` folder to a normal path |
| `git status` doesn't show the app's `data/` package | It was gitignored before the fix — run `git add Kotlin/app/src/main/java/com/negotiateai/app/data/` to commit it |
