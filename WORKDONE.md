1. Investigation — RAG, model, and wiring status

- Checked the model: confirmed  bharatgenai/LegalParam  was downloaded (11GB in  ~/.cache/huggingface/hub ).
- Checked RAG: confirmed  data/legal/  had real law text and 6,723 chunks indexed — but it was running the keyword fallback, not vector search.
- Traced the full chain: frontend (Kotlin) →  POST /api/cases/{id}/negotiate  → Module 4 ( negotiation_ai.py ) → RAG injection into the prompt. Confirmed the plumbing existed end-to-end.
- Found the blockers:  USE_LOCAL_MODEL  was missing from  .env  (so the app always used the rule-based fallback — RAG never actually ran), and section citations showed  General  instead of  Section 15/16 .

2. Made it actually work — model + RAG

- Added  USE_LOCAL_MODEL=true  to  .env .
- Discovered your real environment is  .venv  (has chromadb 1.5.9 + sentence-transformers 5.7.0 + CPU torch; the system Python didn't).
- Fixed RAG code ( AIML/legal_rag.py ):
- Section regex now handles markdown  **15. …**  headers → citations show  Section 15 ,  Section 16  instead of  General .
- Fixed a ChromaDB crash (6,723 chunks > 5,461 batch limit) by batching upserts.
- Rebuilt the vector index — verified a live query for a payment-delay case returns the actual Section 16 (compound interest) text.
- Debugged the model loading (this was the long one):
- transformers 5.15 in  .venv  → segfault/OOM (proved it was RAM: free memory dropped 17GB → 1.5GB during fp16 conversion).
- fp32 + mmap loaded instantly but generation crashed ( 'DynamicCache' object is not subscriptable  — the model's code is 4.x-era).
- transformers 4.48.3 worked — verified it gives real answers ("Section 16 = 24% per annum").
- Downgraded  .venv  to transformers 4.48.3, updated  negotiation_ai.py  to the proven load config (fp32 streaming, refuse transformers ≥5 with a clear error), and pinned  transformers<5  in  requirements_deploy.txt .
- Verified the full Module 4 chain end-to-end: a real mediator response naming your parties (ABC Traders / XYZ Manufacturing), the ₹4.5L claim, 120 days overdue, and citing Section 16.

3. Answered "how to test" and "how to run"

- Gave a step-by-step testing guide (model sanity → Module 4 chain → API via curl → app).
- Gave exact CMD commands for the whole project: backend with  .venv , Android Studio/ gradlew  for the app, emulator note ( 10.0.2.2  is emulator-only), and timing expectations.

4. Negotiation timing — and a bug fix

- Explained the flow: 1st message ~2–3 min (model load + generation), then ~30–90s per message.
- Found + fixed a real bug: the app's OkHttp timeout was 30s — the first slow message would have timed out and appeared to fail. Raised read timeout to 300s in  ApiClient.kt .

5. Model-load frequency — and another fix

- Explained it loaded once per case (each new case re-loaded the 11GB model).
- Fixed it: the model is now a process-wide singleton — loads once per server start, shared by every case, with a lock so concurrent messages queue safely.

6. Login "Internal Server Error" — diagnosed and fixed

- Traced it to your database: 2 legacy accounts with  role = 'BUYER' , which isn't in the current enum → SQLAlchemy  LookupError  → HTTP 500 → app shows "Internal Server Error". (Proved the API was otherwise healthy with fresh accounts.)
- You chose the migration option — updated  buyer@test.com  and  userb@test.com  →  respondent , verified all 10 users load cleanly, and cleaned up my diagnostic test account.
- Confirmed login works end-to-end: register → login (got a real JWT) → authenticated calls all HTTP 200.

Current state

Everything is wired and working: login/register ✅, dashboard ✅, RAG with real section citations ✅, LegalParam generating real answers ✅, load-once-per-server ✅, app timeout fixed ✅, legacy data migrated ✅.

Files changed this session

-  .env  —  USE_LOCAL_MODEL=true 
-  AIML/legal_rag.py  — section regex + batched upserts
-  AIML/negotiation_ai.py  — working load config, transformers<5 guard, process-wide model singleton + lock
-  requirements_deploy.txt  — pinned  transformers<5 
-  Kotlin/.../core/network/ApiClient.kt  — read timeout 30s → 300s
-  .venv  — transformers 5.15 → 4.48.3
-  data/chroma/  — rebuilt vector index
- Supabase DB —  BUYER  →  respondent  data migration

Not changed: any app screens, auth code, or the RAG corpus files themselves.