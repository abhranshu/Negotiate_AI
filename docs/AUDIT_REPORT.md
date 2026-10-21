# NegotiateAI — Infrastructure & AI Audit Report

Audited against the **current working tree** (not the README). Items marked
**[measured]** were executed in this environment; items marked **[estimated]**
are derived from artifact sizes/dependency knowledge and still need runtime
confirmation on the target host.

---

## 1. Executive summary

The repository is a genuine FastAPI + AI/ML platform with five modules and a React
frontend. It is **not** deployment-ready for AWS Free Tier as currently configured:

- Module 1 (voice) runs in **stub mode** (`USE_LOCAL_ASR=false`).
- Module 3 has **pre-trained models present**, but a missing `lightgbm` install can
  push it to a hardcoded fallback.
- Module 4 uses a **1.5B local LLM** → peak RAM far exceeds a 1 GB micro.
- RAG runs the **keyword fallback** (no `chromadb`/`sentence_transformers`).

A safe code pass (fallback labelling, 1-worker default, DB-aware health) plus a
31-test suite were added this session. **[measured: 31 passed]**

## 2. Current architecture

See `docs/AWS_DEPLOYMENT.md §1`. DB is Supabase Postgres via pooler; uploads on
local disk; Alembic migrations at startup.

## 3. AWS Free Tier architecture

See `docs/AWS_DEPLOYMENT.md §5`. Single t3.micro + S3/CloudFront; Supabase instead
of RDS; no NAT/ALB.

## 4. Five-module status

| Module | Current model | Working? | Real ML? | RAM | Latency | Changes | Status |
|---|---|---|---|---|---|---|---|
| M1 Voice | faster-whisper/whisper (tiny) | Endpoint yes | **No — stub** | ~150 MB when on | n/a (stub) | none | ⚠️ STUB |
| M2 Documents | Tesseract + DistilBERT | Yes (stub on failure) | Partial | ~250 MB on demand | seconds | none | ⚠️ Partial |
| M3 Prediction | XGBoost + LightGBM + SHAP | Yes | **Yes — confirmed** | ~200 MB | <1 s warm | `lightgbm` installed; real inference verified | ✅ |
| M4 Negotiation | Qwen2.5-1.5B int8 + Groq + rule-based | Yes | Partial | **1.5–2.5 GB** | seconds | labelled fallback | ⚠️ Heavy |
| M5 Settlement | Template + validator | Yes | Yes (template) | small | fast | none | ✅ |

## 5. Model memory report **[estimated]**

| Model | On disk | Params | dtype | RAM after load | Peak inference |
|---|---|---|---|---|---|
| Qwen2.5-1.5B-Instruct | ~3 GB (download) | 1.5B | int8 | ~1.5–2.5 GB | +0.3–0.5 GB |
| faster-whisper tiny | ~75 MB | 39M | int8 | ~150 MB | ~200 MB |
| DistilBERT classifier | ~250 MB | 66M | fp32 | ~250–300 MB | +50 MB |
| XGBoost settlement clf | 4.6 MB | — | — | ~50 MB | small |
| LightGBM regressors | ~360 KB | — | — | ~20 MB | small |
| RoBERTa sentiment | ~500 MB | 125M | fp32 | ~500 MB | +50 MB |

> Judge by **RAM after load**, not file size — this is why the local LLM is the
> problem.

## 6. Model optimization report

Order applied/available: (1) unused deps, (2) unused models, (3) lazy load,
(4) not loading all models at once, (5) CPU-only torch (already in Dockerfile),
(6) fp16, (7) int8, (8) 4-bit, (9) smaller equivalent, (10) unload after inference.
Current code already does **lazy loading + process-wide caching** (`api/cache.py`).
`LOCAL_MODEL_QUANTIZE=true` (int8) is set.

## 7. Baseline vs optimized results

**Not produced this session.** Producing a real baseline requires running each
model and replaying inputs, which needs the heavy deps installed and time. This is
flagged as outstanding rather than fabricated.

## 8. Test results **[measured]**

`python -m pytest tests -q` → **31 passed, 0 failed** (76 s). Covers health, auth
(incl. malformed JWT), cases (incl. 403 cross-user), documents, voice (stub made
**visible**), prediction, negotiation, settlement negative paths, WebSocket
presence/typing + invalid party, and no-silent-fallback guards.

## 9. Failed tests

None remaining. Initial run had 2 failures + 20 errors, all from `email-validator`
rejecting the special-use `.local` TLD; fixed by using `@example.com`.

## 10. Fixes applied

1. `Dockerfile` — gunicorn `--workers 2` → `--workers ${WORKERS:-1}` (prevents
   duplicate model memory / OOM).
2. `api/main.py` — `/health` now verifies DB reachability (503 when unreachable),
   never ML; warns when `ALLOWED_ORIGINS` contains `*`.
3. `api/routes/predict.py` + `api/schemas/case.py` — fallback estimates are now
   explicitly labelled (`is_fallback`, `recommendation` marked `[FALLBACK …]`) and
   logged, instead of silently looking like a model prediction.
4. `api/routes/negotiate.py` + schema — `_FALLBACK_RESULT` now carries
   `is_fallback: true`.
5. `tests/` — new suite (the repo previously had no tests).

## 11. Files changed

- `Dockerfile`
- `api/main.py`
- `api/routes/predict.py`
- `api/routes/negotiate.py`
- `api/schemas/case.py`
- `tests/conftest.py`, `tests/test_health.py`, `tests/test_auth.py`,
  `tests/test_cases.py`, `tests/test_documents.py`, `tests/test_voice.py`,
  `tests/test_prediction.py`, `tests/test_negotiation.py`,
  `tests/test_settlement.py`, `tests/test_websocket.py`,
  `tests/test_no_silent_fallback.py`
- `docs/AWS_DEPLOYMENT.md`, `docs/AUDIT_REPORT.md`

## 12. Environment variables required

`DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`,
`USE_LOCAL_MODEL`, `LOCAL_MODEL_ID`, `LOCAL_MODEL_QUANTIZE`, `USE_EXTERNAL_LLM`,
`GROQ_API_KEY`, `USE_LOCAL_ASR`, `UVICORN_WORKERS`, `UPLOAD_DIR`,
`MAX_FILE_SIZE_MB`, `ALLOWED_ORIGINS`, `PROXY_COUNT`, `HOST`, `PORT`.
Production: `ALLOWED_ORIGINS` must list real origins; `USE_LOCAL_MODEL=false` for
Free Tier.

## 13. AWS services required

EC2 (micro), EBS, S3 + CloudFront (frontend), ECR (image), optional Elastic IP.

## 14. AWS services NOT required

RDS, ElastiCache, OpenSearch, Nat Gateway, ALB, SageMaker, paid ECS/Fargate.

## 15. Estimated resource usage

See `docs/AWS_DEPLOYMENT.md §3`. Path A peak ~1.0–1.3 GB; Path B ~3–4.5 GB.

## 16. Deployment steps

See `docs/AWS_DEPLOYMENT.md §6`.

## 17. Rollback steps

See `docs/AWS_DEPLOYMENT.md §8`.

## 18. Known limitations

- ✅ **Resolved** — the Module 3 pickles were saved with scikit-learn **1.8.0** but the
  runtime was **1.7.2**, emitting `InconsistentVersionWarning`. scikit-learn is now
  1.8.0 and is **pinned (`==1.8.0`) in `requirements.txt` and `requirements_deploy.txt`**.
  The warning is gone and predictions are unchanged (`is_fallback=false`, real output).
- ✅ **Resolved** — the XGBoost "serialized model" advisory is **removed**. The
  settlement classifier is now persisted in XGBoost's **native format**
  (`models/native/*.ubj` + a JSON sidecar of the Platt calibration params) via
  `Booster.save_model`, so loading never unpickles an XGBoost object. This required
  **no retraining**: the native model reproduces the pickle numerically (max abs
  diff `6.4e-08`, float32-level; `allclose` at `1e-9`) and the engine now emits
  **0 warnings** on load. `scripts/reexport_module3.py` performs the conversion, and
  the trainer exports the native format automatically on every future retrain.

- Module 1 is a stub until `USE_LOCAL_ASR=true` + an ASR engine is installed.
- RAG is keyword-based until `chromadb` + `sentence-transformers` are installed.
- Uploaded files are on ephemeral disk in containers (lost on restart).
- Module 4 with the local LLM does **not** fit Free Tier.
- Baseline-vs-optimized model quality benchmarks are **not yet run**.
- No AWS credentials here → AWS steps are documented, not executed.

## 19. Security risks

- `.env` is correctly git-ignored **[measured]**, but contains live Supabase
  credentials — rotate if ever exposed.
- Default `SECRET_KEY` and `ALLOWED_ORIGINS=["*"]` are dev-only; must be set.
- `alembic.ini` embeds a fallback `sqlalchemy.url` (SQLite) — harmless but not a
  production default.
- Health endpoint leaks DB error text on failure (consider trimming in prod).

## 20. Cost risks

NAT Gateway (~$32/mo), ALB (~$16/mo), unattached Elastic IPs, RDS after 12 months,
ECR over 500 MB, S3/CloudFront after 12 months. Mitigate with a billing alarm.

## 21. FINAL GO / NO-GO

### **NO-GO** for a blanket "deploy everything to Free Tier" claim.

Specifically:
- ❌ **Module 4 (local Qwen) cannot run within the tested Free Tier (1 GB) budget.**
  Smallest viable options: (a) Path A with `USE_LOCAL_MODEL=false` + existing
  external LLM/rule-based mode on a micro; or (b) Path B on a paid `t3.small+`.
- ❌ **Module 1 is currently a stub** — do not claim voice works until real ASR is
  enabled and tested.
- ✅ **Module 3 is confirmed real**: with `lightgbm 4.7.0` installed, the saved models
  load (`CalibratedClassifierCV` + 2× `LGBMRegressor`) and `/predict` returns
  `is_fallback=false` with genuine, feature-dependent output.
- ⚠️ **RAG** is on the keyword fallback, not vector search.

A **conditional GO** applies to Path A once: `USE_LOCAL_MODEL=false` is set, real
origins replace `*`, `lightgbm` is installed, and `docker stats` confirms peak RAM
under the instance limit.
