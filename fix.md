# NegotiateAI — Fix List (audit session, Oct 2026)
> No code changed to create this file. PROBLEM -> EVIDENCE -> FIX -> PAPER.

## P0 — Paper-blockers

### 1. msme_samadhaan.csv has no provenance
- PROBLEM: 10k rows, 17 cols, 2017-2025, single commit 8f914d8. No script writes that schema. generate_synthetic_cases() outputs a DIFFERENT 18-col schema.
- EVIDENCE: outcome_prediction.py:197-267 vs CSV header; grep msme_samadhaan = reader only (:272).
- FIX: create scripts/make_msme_samadhaan.py (seed 42, n=10000, 17-col schema) -> data/msme_samadhaan_v2.csv; add data/DATASET_CARD.md with SHA-256 + 3 Samadhaan dashboard aggregates.
- PAPER: replace 1247 scraped/RTI with proxy-corpus + generator + hash.

### 2. Label caveat missing (r~0.43)
- PROBLEM: settled = mutually settled in status (:293-295); doc_score 0.532 neg vs 0.706 pos, corr 0.426. AUC 0.789 is in-corpus fit.
- FIX: disclose; add temporal holdout (train <=2022, test >=2023).
- PAPER: labels file-given 66.1% pos; doc_score r~0.43; no external validation.

### 3. Sentiment: name keyword fallback
- PROBLEM: tries cardiffnlp/twitter-roberta (negotiation_ai.py:123-129), 3-label map (:149-154, FRUSTRATED/CONCILIATORY unreachable); log backend_model.log:18 = keyword heuristic. models/sentiment_roberta/ absent.
- FIX: paper names SENTIMENT_KEYWORDS (:112-121); or train + wire sentiment_roberta.
- PAPER: remove fine-tuned 5-class RoBERTa, F1 0.89, 3500 msgs, kappa.

### 4. AUC 0.843 / DeLong / 0.791 — do not use
- PROBLEM: re-run prints 0.789 +- 0.012 (5-fold CV, cv_out.txt). 0.843/0.791/DeLong = zero hits.
- FIX: use 0.789+-0.012; run held-out + DeLong to earn rest.

### 5. RAG eval (P@5/MRR/50 queries/co-retrieval Eq.4) — absent
- PROBLEM: legal_rag.py = TF-IDF x boost, top-k=3, no rerank/hybrid/BM25. Corpus = MSMED + Companies Act 2013 (wrong act), 0 orders, 0 queries.
- FIX: swap A2013-18.md for Contract Act + 20-50 orders; 50-question set; ranx P@5/MRR; or remove Eq.4.

### 6. 347 sessions / 76.9% / 4.2d / 78.3% — absent
- PROBLEM: no generator, no JSON/CSV/DB. Only demo_phase2.py (1 case).
- FIX: scripts/simulate_negotiations.py (347 x strategies, max 10 rounds) -> output/negotiation_sims.json, or delete.

### 7. Table II + user study + Acknowledgment — no source
- PROBLEM: zero hits for costs/durations/participants; research_Paper/ empty.
- FIX: DELETE Table II numbers + user-study + participants sentence; or external cites per row.

### 8. Mediator math (EWMA 0.7 / 0.75 / 5% stagnation, Eq.3/Alg.2) — absent
- PROBLEM: real logic = is_deadlock() last-3 hostile/frustrated, streak>=2 -> suggest_mediator_proposal, HOSTILE -> de-escalate, zopa_exists() crossover. No EWMA/0.75/stagnation.
- FIX: replace Eq.3/Alg.2 with real rules.

### 9. Settlement PDF + SHA-256 — absent
- PROBLEM: settlement_generator.py = text template + validator; route returns JSON. Zero reportlab/hashlib hits.
- FIX: implement (reportlab + hashlib.sha256) or remove claims.

### 10. Socket.IO ref — wrong dep
- PROBLEM: native FastAPI WebSocket (ws_manager.py: broadcast_public/send_private). No socket.io dep. Redis absent (status.md:67 in-memory). DB default SQLite (config.py:21).
- FIX: cite RFC 6455 + FastAPI WS; paper: WS broadcast + party-filtered private send, in-memory cap 50, SQLite default / Postgres optional.

### 11. 18 features — wrong, it is 16
- PROBLEM: FeatureEngineer.to_array() = 16 cols (claim, log_claim, overdue, prev_pay, inv_count, doc_score, contract, delivery, claimant_size, respondent_size, prior, industry, dtype, state, msefc, days_since).
- FIX: correct to 16 everywhere.

### 12. Languages 12 supported — overclaim
- PROBLEM: 12 codes declared (voice has ur; translator has as+en), ASR config 9, only hi/ta smoke samples. No hi/ta test/log.
- FIX: 12 codes exposed, hi/ta smoke-tested, full eval future work.

### 13. OOM + NumPy (deploy crash)
- PROBLEM: negotiation_ai.py:397 low_cpu_mem_usage=on_gpu = False on CPU -> legacy fp32 loader; Dockerfile torch==2.2.2+cpu then numpy->2.4.6 (_ARRAY_API break).
- FIX: low_cpu_mem_usage=True; pin numpy>=1.26,<2; avoid quantize_dynamic on 1.5B in small container (~9.2GB peak).

## P1 — Should fix

14. settlement_pct = 0.75 constant -> MAE 0.000 meaningless (:340-342). Derive or drop.
15. days_since_dispute = delay_days dup; msefc=1, prev_pay=0, micro constants (:358-364). Disclose.
16. FINE_TUNE.md/docstrings cite Craigslist/MultiWOZ/GoEmotions as trained — never loaded. Downgrade to future work.
17. README claims DistilBERT fine-tuned / RoBERTa-GoEmotions / Mistral-7B — none in repo. Soften.
18. No train_test_split for Module 3 — CV only. Add held-out.
19. predict.py:45 cold-starts on synthetic n=3000 if models missing. Document/disable in prod.
20. data/legal/A2013-18.md (Companies Act) indexed — swap for Contract Act.

## P2 — Nice to have

21. models/sentiment_roberta/ + negotiator_lora/ absent though docs promise. Train or remove.
22. train_whisper.py absent though get_whisper_finetune_config() references it.
23. download_indictrans2.py saves ./data/indictrans2 but service loads HF hub — align.
24. cv_out.txt is my re-run log — keep or delete before submit.
25. .env secret pattern — ensure no real keys committed.

## Safe paper patches

- Dataset: Samadhaan-schema proxy, 10k filings, 17 attrs, 2017-2025, no PII, synthetic + generator (seed 42) + SHA-256; labels file-given 66.1% pos, doc_score r~0.43; CV AUC 0.789+-0.012 in-corpus only.
- Sentiment: evaluated path = keyword scorer (SENTIMENT_KEYWORDS); cardiffnlp attempted, not loaded in logged run.
- Transport: native WebSocket broadcast + party-filtered private send, in-memory cap 50, SQLite default / Postgres optional, no Redis/Socket.IO.
- Removed until measured: 1247/3500/kappa/0.843/DeLong/0.89/0.88-OCR/50-query P@5-MRR/347-session/Table II/user study/EWMA/co-retrieval/ReportLab-SHA256.
