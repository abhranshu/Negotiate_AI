# NegotiateAI — Data Sources & Collection Guide
# ===============================================
# A complete map of where to get training data for each module.

# ══════════════════════════════════════════════════════════════════
# MODULE 1 — Multilingual Voice (ASR Fine-tuning)
# ══════════════════════════════════════════════════════════════════

## Primary (free, open-access)
- AI4Bharat IndicSUPERB          https://huggingface.co/datasets/ai4bharat/indicsuperb
  • ~120hrs speech across 12 Indian languages, labelled transcripts
  • Best for: Whisper fine-tuning baseline

- Mozilla Common Voice (Hindi/Tamil/Telugu/Bengali)
  https://commonvoice.mozilla.org/en/datasets
  • Download specific language packs (~500MB–3GB each)
  • Best for: accent diversity

- Google FLEURS (Indian languages)  https://huggingface.co/datasets/google/fleurs
  • 102 languages including 10 Indian ones, ~12hrs each

- AI4Bharat Shrutilipi             https://huggingface.co/datasets/ai4bharat/Shrutilipi
  • 6400+ hrs broadcast speech in 12 Indian languages — BEST RESOURCE

## NER Labels (for form-filling)
- Collect 300–500 MSME complaint texts (from MSME Samadhan portal)
- Manually annotate with BIO tags using Label Studio (free):
  https://labelstud.io
- Entity types: CLAIMANT, RESPONDENT, AMOUNT, DATE, INVOICE_NO, DISPUTE_TYPE

# ══════════════════════════════════════════════════════════════════
# MODULE 2 — Document Intelligence (Classifier + OCR)
# ══════════════════════════════════════════════════════════════════

## Synthetic data (generate immediately — no approval needed)
- Use: generate_training_dataset() in document_intelligence.py
- Faker + reportlab creates labelled invoice/PO/contract PDFs
- Target: 500 samples per class × 8 classes = 4000 documents

## Real data
- MSME Samadhan public filings:    https://samadhaan.msme.gov.in
  • Download sample case documents (PDFs) for model validation

- RVL-CDIP document dataset:       https://huggingface.co/datasets/rvl_cdip
  • 400,000 labelled document images (16 classes) — good for pre-training

- FUNSD (form understanding):      https://guillaumejaume.github.io/FUNSD/
  • Form field extraction benchmark

- IIT-Bombay Legal NLP corpus:     https://github.com/Legal-NLP-EkStep
  • Indian legal text for NLP models

# ══════════════════════════════════════════════════════════════════
# MODULE 3 — Outcome Prediction (XGBoost/LightGBM)
# ══════════════════════════════════════════════════════════════════

## Best path: RTI Request (takes 30 days, costs ₹10)
  File online at: https://rtionline.gov.in
  Ministry: Ministry of Micro, Small and Medium Enterprises
  Ask for: "Anonymised summary data of MSEFC cases filed 2018–2023
            including: state, industry sector, claim amount, outcome
            (settled/arbitrated), settlement amount, resolution days"

## Immediate alternatives
- MSME Samadhan portal statistics: https://samadhaan.msme.gov.in
  • Public aggregate data, useful for base rates

- Arbitration case data (proxy):   https://mhc.tn.gov.in (Madras HC)
  • Commercial court outcomes for small claims

- World Bank Doing Business India: https://data.worldbank.org/country/india
  • Contract enforcement metrics, useful for BATNA calibration

- SIDBI MSME Pulse (quarterly):    https://www.sidbi.in/en/publications
  • Receivables data, sector-wise payment delays — helps feature engineering

## Synthetic bootstrap (use immediately)
  generate_synthetic_cases() in outcome_prediction.py
  • Generates 5000 cases with rules derived from published MSEFC statistics
  • Replace incrementally as real data arrives via RTI

# ══════════════════════════════════════════════════════════════════
# MODULE 4 — Negotiation AI (LLM + Sentiment)
# ══════════════════════════════════════════════════════════════════

## Sentiment model training data
- GoEmotions:                      https://huggingface.co/datasets/go_emotions
  • 58K Reddit comments, 27 emotion labels — fine-tune for negotiation context

- EmoBank:                         https://github.com/JULIELab/EmoBank
  • Valence-Arousal-Dominance — useful for hostility detection

- SemEval 2018 Task 1 (Emotion):   https://huggingface.co/datasets/sem_eval_2018_task_1
  • Multi-label emotion, good for conflict signal detection

## Negotiation dialogue data
- CraigslistBargain:               https://huggingface.co/datasets/craigslist_bargains
  • 6682 human-human negotiation dialogues with offers — BEST for bargaining

- MultiWOZ 2.4:                    https://huggingface.co/datasets/multi_woz_v22
  • Task-oriented dialogues — good for moderator response style

- DealOrNoDeal:                    https://github.com/facebookresearch/end-to-end-negotiator
  • Facebook negotiation dataset with outcomes

## LLM fine-tuning (moderator)
  - Curate ~500 MSEFC-style dialogues manually
  - Annotate each mediator turn with: mediator_move ∈
    {reframe, validate, suggest_compromise, cite_law, summarise, close_deal}
  - Use TRL SFTTrainer on Mistral-7B-Instruct

## Translation
- IndicTrans2 (AI4Bharat):         https://huggingface.co/ai4bharat/indictrans2-en-indic-dist-200M
  • Pre-trained, no fine-tuning needed for standard use
  • 22 Indian languages ↔ English, best available

# ══════════════════════════════════════════════════════════════════
# MODULE 5 — Settlement Generation (Legal LLM)
# ══════════════════════════════════════════════════════════════════

## Legal templates and precedents
- MSEFC settlement orders (public): https://samadhaan.msme.gov.in
  • Download PDF conciliation orders — these are your ground truth templates

- India Code (Indian Contract Act):  https://indiacode.nic.in/handle/123456789/2187
  • MSMED Act text:                  https://indiacode.nic.in/handle/123456789/1556

- InLegalBench:                      https://huggingface.co/datasets/Exploration-Lab/InLegalBench
  • Indian legal NLP benchmark, useful for evaluation

- NLTA (National Legal Tech Alliance): Contact for sample agreement corpus
  https://nlta.in

## Fine-tuning approach
  1. Collect 200–500 real MSEFC settlement orders (PDFs)
  2. Extract structured fields: parties, amount, schedule, clauses
  3. Fine-tune: Mistral-7B-Instruct with LoRA on (case_context → agreement_text) pairs
  4. Keep template system as guardrail — LLM only fills non-templated sections

# ══════════════════════════════════════════════════════════════════
# DATA COLLECTION PRIORITY MATRIX
# ══════════════════════════════════════════════════════════════════
#
#  Module  | Can start immediately?         | Need RTI/MOU?
#  ──────────────────────────────────────────────────────────────
#  M1 ASR  | YES — AI4Bharat/FLEURS ready   | No
#  M2 Docs | YES — generate synthetic       | No
#  M3 Pred | YES — synthetic bootstrap      | YES (for real MSEFC data)
#  M4 Neg  | YES — CraigslistBargain        | No (curate 500 dialogues)
#  M5 Settle| YES — template works now      | YES (real MSEFC orders)
#
# Start with synthetic/public data. File RTI on Day 1 in parallel.
# Real MSEFC data will arrive ~Month 2 and can be used to retrain.
