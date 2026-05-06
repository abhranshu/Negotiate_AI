"""
Module 1 — Multilingual Voice Input & Automated Form Population
================================================================
Pipeline:
  Audio (12 Indian languages)
    → Whisper ASR  → raw transcript
    → IndicTrans2  → English translation
    → spaCy NER    → structured entities
    → Form fields  (claimant, respondent, invoice_amount, due_date, dispute_type)

Data sources:
  - AI4Bharat IndicSUPERB  (https://huggingface.co/datasets/ai4bharat/indicsuperb)
  - Common Voice Hindi/Tamil/Telugu  (https://commonvoice.mozilla.org)
  - FLEURS Indian languages  (https://huggingface.co/datasets/google/fleurs)
"""

import re
import json
import torch
import spacy
import whisper
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Optional
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    pipeline as hf_pipeline,
)


# ─── Data classes ────────────────────────────────────────────────────────────

SUPPORTED_LANGUAGES = {
    "hi": "Hindi",   "ta": "Tamil",    "te": "Telugu",  "bn": "Bengali",
    "mr": "Marathi", "kn": "Kannada",  "ml": "Malayalam","gu": "Gujarati",
    "pa": "Punjabi", "or": "Odia",     "as": "Assamese","ur": "Urdu",
}

@dataclass
class DisputeFormFields:
    claimant_name:     Optional[str]   = None
    respondent_name:   Optional[str]   = None
    invoice_number:    Optional[str]   = None
    invoice_amount:    Optional[float] = None
    currency:          str             = "INR"
    due_date:          Optional[str]   = None
    dispute_type:      Optional[str]   = None
    description:       Optional[str]   = None
    detected_language: Optional[str]   = None
    confidence:        float           = 0.0
    missing_fields:    list            = field(default_factory=list)

    def validate(self) -> list[str]:
        required = ["claimant_name", "respondent_name",
                    "invoice_amount", "dispute_type"]
        return [f for f in required if getattr(self, f) is None]


# ─── ASR: Whisper fine-tuned on Indian languages ─────────────────────────────

class IndianASR:
    """
    Wraps OpenAI Whisper (medium or large-v3).
    For production: fine-tune on AI4Bharat IndicSUPERB dataset.
    Fine-tuning script: see train_whisper.py
    """

    def __init__(self, model_size: str = "medium"):
        print(f"[ASR] Loading Whisper {model_size}...")
        self.model = whisper.load_model(model_size)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> dict:
        """
        Transcribe audio. If language is None, Whisper auto-detects.
        Returns: {text, language, language_probability}
        """
        options = {
            "task": "transcribe",
            "language": language,
            "fp16": self.device == "cuda",
            "beam_size": 5,
            "best_of": 5,
            "temperature": (0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
        }
        result = self.model.transcribe(audio_path, **options)
        detected_lang = result.get("language", "unknown")
        lang_prob = result.get("language_probability", 0.0)

        print(f"[ASR] Detected: {detected_lang} (conf={lang_prob:.2f})")
        return {
            "text": result["text"].strip(),
            "language": detected_lang,
            "language_probability": lang_prob,
            "segments": result.get("segments", []),
        }

    def transcribe_to_english(self, audio_path: str) -> dict:
        """Direct Whisper translation to English (works for most Indian langs)."""
        result = self.model.transcribe(audio_path, task="translate", fp16=False)
        return {"text": result["text"].strip(), "language": result.get("language")}


# ─── NER: Legal entity extraction ────────────────────────────────────────────

DISPUTE_TYPES = [
    "delayed_payment", "non_payment", "short_payment",
    "quality_dispute", "quantity_dispute", "contract_breach",
]

DISPUTE_KEYWORDS = {
    "delayed_payment": ["delayed", "overdue", "late payment", "not paid on time"],
    "non_payment":     ["not paid", "no payment", "unpaid", "haven't received"],
    "short_payment":   ["partial", "short payment", "less amount", "deducted"],
    "quality_dispute": ["defective", "damaged", "poor quality", "rejected"],
    "quantity_dispute":["wrong quantity", "short supply", "missing items"],
    "contract_breach": ["violated", "breach", "not delivered", "cancelled"],
}


class LegalNER:
    """
    Named Entity Recognition for MSME dispute form fields.
    Uses a BERT model fine-tuned on Indian legal + financial text.

    For production: fine-tune 'ai4bharat/indic-bert' on labelled MSEFC
    complaint texts with BIO tags for CLAIMANT, RESPONDENT, AMOUNT,
    DATE, INVOICE_NO, DISPUTE_TYPE.

    Training data: annotate ~2000 sample ODR complaint texts.
    """

    def __init__(self, model_name: str = "dslim/bert-base-NER"):
        print(f"[NER] Loading NER model: {model_name}")
        self.ner_pipeline = hf_pipeline(
            "ner",
            model=model_name,
            aggregation_strategy="simple",
            device=0 if torch.cuda.is_available() else -1,
        )
        # Regex fallbacks for structured patterns
        self._amount_re  = re.compile(
            r"(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d{1,2})?)"
            r"|(\d[\d,]*(?:\.\d{1,2})?)\s*(?:lakhs?|crores?|rupees?)",
            re.IGNORECASE,
        )
        self._date_re    = re.compile(
            r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
            r"|\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})",
            re.IGNORECASE,
        )
        self._invoice_re = re.compile(
            r"\b(?:invoice|inv|bill)\s*[#\-]?\s*([A-Z0-9\-/]+)",
            re.IGNORECASE,
        )

    def extract(self, text: str) -> dict:
        entities = {"PERSON": [], "ORG": [], "MONEY": [], "DATE": [], "MISC": []}

        # Transformer NER
        raw = self.ner_pipeline(text)
        for ent in raw:
            label = ent["entity_group"]
            if label in entities:
                entities[label].append(ent["word"])

        # Regex extraction
        amounts  = self._amount_re.findall(text)
        dates    = self._date_re.findall(text)
        invoices = self._invoice_re.findall(text)

        # Parse amounts — take the largest as invoice amount
        parsed_amounts = []
        for a, b in amounts:
            raw_num = (a or b).replace(",", "")
            try:
                val = float(raw_num)
                if "lakh" in text.lower():
                    val *= 100_000
                elif "crore" in text.lower():
                    val *= 10_000_000
                parsed_amounts.append(val)
            except ValueError:
                pass

        return {
            "persons":        entities["PERSON"],
            "organisations":  entities["ORG"],
            "amounts":        sorted(parsed_amounts, reverse=True),
            "dates":          [d[0] or d[1] for d in dates],
            "invoice_numbers": invoices,
        }

    def classify_dispute_type(self, text: str) -> tuple[str, float]:
        text_lower = text.lower()
        scores = {}
        for dtype, keywords in DISPUTE_KEYWORDS.items():
            scores[dtype] = sum(1 for kw in keywords if kw in text_lower)
        best = max(scores, key=scores.get)
        total = sum(scores.values()) or 1
        return best, scores[best] / total


# ─── Main pipeline ────────────────────────────────────────────────────────────

class VoiceToFormPipeline:
    """End-to-end: audio file → populated DisputeFormFields."""

    def __init__(self, whisper_size: str = "medium"):
        self.asr = IndianASR(whisper_size)
        self.ner = LegalNER()

    def process(self, audio_path: str, language: Optional[str] = None) -> DisputeFormFields:
        form = DisputeFormFields()

        # Step 1 — ASR
        result      = self.asr.transcribe(audio_path, language)
        transcript  = result["text"]
        form.detected_language = result["language"]
        form.confidence        = result["language_probability"]

        # Step 2 — Translate to English if non-English detected
        if result["language"] not in ("en", "english"):
            en_result  = self.asr.transcribe_to_english(audio_path)
            en_text    = en_result["text"]
        else:
            en_text = transcript

        print(f"[Pipeline] Transcript (EN): {en_text[:120]}...")
        form.description = transcript   # store original-language description

        # Step 3 — NER
        entities = self.ner.extract(en_text)

        # Assign entities to form fields
        persons = entities["persons"]
        orgs    = entities["organisations"]
        all_names = persons + orgs

        if len(all_names) >= 2:
            form.claimant_name   = all_names[0]
            form.respondent_name = all_names[1]
        elif len(all_names) == 1:
            form.claimant_name   = all_names[0]

        if entities["amounts"]:
            form.invoice_amount = entities["amounts"][0]

        if entities["dates"]:
            form.due_date = entities["dates"][0]

        if entities["invoice_numbers"]:
            form.invoice_number = entities["invoice_numbers"][0]

        # Step 4 — Dispute type classification
        dtype, conf = self.ner.classify_dispute_type(en_text)
        form.dispute_type = dtype if conf > 0.0 else None

        # Step 5 — Validate & flag missing fields
        form.missing_fields = form.validate()

        return form

    def to_odr_json(self, form: DisputeFormFields) -> str:
        """Serialize form for ODR portal submission."""
        return json.dumps(asdict(form), indent=2, ensure_ascii=False)


# ─── Whisper fine-tuning scaffold ────────────────────────────────────────────

def get_whisper_finetune_config() -> dict:
    """
    Returns training config for fine-tuning Whisper on IndicSUPERB.

    Dataset: https://huggingface.co/datasets/ai4bharat/indicsuperb
    Run:     python train_whisper.py --config whisper_finetune_config.json

    Uses: HF Seq2SeqTrainer + WhisperFeatureExtractor
    """
    return {
        "model_name_or_path": "openai/whisper-medium",
        "dataset_name":       "ai4bharat/indicsuperb",
        "dataset_config_name": "all",
        "language":           "hi,ta,te,bn,mr,kn,ml,gu,pa",
        "task":               "transcribe",
        "num_train_epochs":   5,
        "per_device_train_batch_size": 8,
        "gradient_accumulation_steps": 4,
        "learning_rate":      1e-5,
        "warmup_steps":       500,
        "max_steps":          10000,
        "generation_max_length": 225,
        "save_steps":         1000,
        "eval_steps":         1000,
        "logging_steps":      100,
        "load_best_model_at_end": True,
        "metric_for_best_model": "wer",
        "greater_is_better":  False,
        "push_to_hub":        False,
        "output_dir":         "./whisper-indian-finetuned",
        "fp16":               True,
    }


# ─── Quick test ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Smoke test with synthetic text (no audio file needed)
    ner = LegalNER()
    sample = (
        "My company Sharma Textiles has not received payment of INR 4,50,000 "
        "from Reddy Garments for invoice INV-2024-892 due on 15/03/2024. "
        "The amount is overdue by 120 days."
    )
    entities = ner.extract(sample)
    dtype, conf = ner.classify_dispute_type(sample)
    print("Entities:", json.dumps(entities, indent=2))
    print(f"Dispute type: {dtype} (conf={conf:.2f})")
