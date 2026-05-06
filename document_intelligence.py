"""
Module 2 — Document Intelligence & Case Analysis
=================================================
Pipeline:
  Uploaded PDFs / images
    → OCR (Tesseract / Google Doc AI)
    → BERT document-type classifier
    → Gap detection (required docs vs submitted)
    → Case Summary (for Modules 3 & 4)

Data sources:
  - MSME Samadhan portal sample filings (https://samadhaan.msme.gov.in)
  - Indian court document datasets (ILDC):
      https://huggingface.co/datasets/coastalcph/multi_eurlex (for transfer)
  - Synthetic invoice/PO data: use Faker + reportlab to generate labelled docs
  - IIT-Bombay legal NLP corpus: https://github.com/Legal-NLP-EkStep
"""

import re
import json
import torch
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from PIL import Image
import pytesseract
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    pipeline as hf_pipeline,
)
from sklearn.preprocessing import LabelEncoder
import joblib


# ─── Document taxonomy ───────────────────────────────────────────────────────

DOC_TYPES = [
    "invoice",
    "purchase_order",
    "delivery_receipt",
    "contract",
    "payment_receipt",
    "bank_statement",
    "correspondence",
    "other",
]

# Required documents per dispute sub-category
REQUIRED_DOCS = {
    "delayed_payment":  ["invoice", "purchase_order", "delivery_receipt"],
    "non_payment":      ["invoice", "purchase_order", "delivery_receipt", "contract"],
    "short_payment":    ["invoice", "payment_receipt", "bank_statement"],
    "quality_dispute":  ["invoice", "delivery_receipt", "contract"],
    "quantity_dispute": ["invoice", "delivery_receipt", "purchase_order"],
    "contract_breach":  ["contract", "invoice", "correspondence"],
}


@dataclass
class DocumentAnalysisResult:
    doc_path:      str
    doc_type:      str
    confidence:    float
    extracted_text: str
    key_fields:    dict = field(default_factory=dict)
    is_valid:      bool = True
    issues:        list = field(default_factory=list)


@dataclass
class CaseSummary:
    dispute_type:       str
    claimant:           Optional[str]
    respondent:         Optional[str]
    total_claim_amount: Optional[float]
    documents_submitted: list
    missing_documents:  list
    flagged_issues:     list
    case_strength:      str       # "strong" | "moderate" | "weak"
    summary_text:       str


# ─── OCR Layer ───────────────────────────────────────────────────────────────

class DocumentOCR:
    """
    Tesseract-based OCR with Indian language support.
    For production: swap Tesseract with Google Document AI for better accuracy.

    Install: sudo apt install tesseract-ocr tesseract-ocr-hin tesseract-ocr-tam
    """

    TESSERACT_LANG_MAP = {
        "hi": "hin", "ta": "tam", "te": "tel", "bn": "ben",
        "mr": "mar", "kn": "kan", "ml": "mal", "gu": "guj",
        "en": "eng",
    }

    def extract_text(self, file_path: str, language: str = "en") -> str:
        path = Path(file_path)
        tess_lang = self.TESSERACT_LANG_MAP.get(language, "eng")

        if path.suffix.lower() == ".pdf":
            return self._extract_from_pdf(str(path), tess_lang)
        else:
            return self._extract_from_image(str(path), tess_lang)

    def _extract_from_image(self, path: str, lang: str) -> str:
        img = Image.open(path)
        config = f"--oem 3 --psm 6 -l {lang}+eng"
        return pytesseract.image_to_string(img, config=config).strip()

    def _extract_from_pdf(self, path: str, lang: str) -> str:
        """Convert PDF pages to images and OCR each."""
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(path, dpi=200)
            texts  = [pytesseract.image_to_string(img, lang=lang) for img in images]
            return "\n\n".join(texts).strip()
        except ImportError:
            raise RuntimeError("Install pdf2image: pip install pdf2image")


# ─── Document Classifier ─────────────────────────────────────────────────────

class DocumentClassifier:
    """
    Fine-tuned DistilBERT for document type classification.

    Training data: ~500 labelled documents per class (4000 total)
    - Positive samples: real invoice/PO/contract PDFs
    - Synthetic: generated via Faker + reportlab (see generate_synthetic_docs.py)

    Base model: distilbert-base-uncased (fast inference)
    For multilingual: xlm-roberta-base
    """

    def __init__(self, model_path: str = "distilbert-base-uncased"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model     = AutoModelForSequenceClassification.from_pretrained(
            model_path, num_labels=len(DOC_TYPES)
        )
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit(DOC_TYPES)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    def classify(self, text: str, max_length: int = 512) -> tuple[str, float]:
        """Returns (doc_type, confidence)."""
        # Use first 512 tokens (header of document is most informative)
        inputs = self.tokenizer(
            text[:2000],
            return_tensors="pt",
            truncation=True,
            max_length=max_length,
            padding=True,
        ).to(self.device)

        with torch.no_grad():
            logits = self.model(**inputs).logits
            probs  = torch.softmax(logits, dim=-1).cpu().numpy()[0]

        pred_idx  = int(np.argmax(probs))
        confidence = float(probs[pred_idx])
        doc_type   = DOC_TYPES[pred_idx]
        return doc_type, confidence

    def extract_key_fields(self, text: str, doc_type: str) -> dict:
        """Regex-based field extraction per document type."""
        fields = {}

        # Universal patterns
        amount_re  = re.compile(r"(?:total|amount|value)[:\s]*(?:INR|Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)", re.I)
        date_re    = re.compile(r"(?:date|dated?)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", re.I)
        gst_re     = re.compile(r"\b(\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1})\b")
        pan_re     = re.compile(r"\b([A-Z]{5}\d{4}[A-Z]{1})\b")

        m = amount_re.search(text)
        if m:
            fields["amount"] = float(m.group(1).replace(",", ""))

        m = date_re.search(text)
        if m:
            fields["date"] = m.group(1)

        m = gst_re.search(text)
        if m:
            fields["gstin"] = m.group(1)

        m = pan_re.search(text)
        if m:
            fields["pan"] = m.group(1)

        if doc_type == "invoice":
            inv_re = re.compile(r"(?:invoice|inv)[#\s\-]*([A-Z0-9\-/]+)", re.I)
            m = inv_re.search(text)
            if m:
                fields["invoice_number"] = m.group(1)

        elif doc_type == "purchase_order":
            po_re = re.compile(r"(?:P\.?O\.?|purchase order)[#\s\-]*([A-Z0-9\-/]+)", re.I)
            m = po_re.search(text)
            if m:
                fields["po_number"] = m.group(1)

        return fields


# ─── Gap Detection ────────────────────────────────────────────────────────────

class GapDetector:
    """
    Compares submitted documents against required set for dispute sub-category.
    Produces a prioritised missing-document checklist.
    """

    def detect_gaps(
        self,
        submitted_doc_types: list[str],
        dispute_type: str,
    ) -> dict:
        required  = set(REQUIRED_DOCS.get(dispute_type, []))
        submitted = set(submitted_doc_types)
        missing   = required - submitted
        extra     = submitted - required

        priority = []
        for doc in missing:
            if doc in ("invoice", "contract"):
                priority.append({"document": doc, "priority": "critical"})
            elif doc in ("purchase_order", "delivery_receipt"):
                priority.append({"document": doc, "priority": "high"})
            else:
                priority.append({"document": doc, "priority": "medium"})

        priority.sort(key=lambda x: ["critical","high","medium"].index(x["priority"]))

        return {
            "missing":          priority,
            "submitted":        list(submitted),
            "extra_documents":  list(extra),
            "completeness_pct": round(len(submitted & required) / max(len(required), 1) * 100, 1),
        }


# ─── Summarisation ───────────────────────────────────────────────────────────

class CaseSummariser:
    """
    Generates a structured case summary using extractive + abstractive methods.
    Uses a summarisation model fine-tuned on legal text.

    For production: fine-tune 'facebook/bart-large-cnn' on MSEFC case descriptions.
    Base (zero-shot): 'philschmid/bart-large-cnn-samsum' works reasonably.
    """

    def __init__(self):
        self.summariser = hf_pipeline(
            "summarization",
            model="sshleifer/distilbart-cnn-12-6",
            device=0 if torch.cuda.is_available() else -1,
        )

    def summarise(self, text: str, max_length: int = 150) -> str:
        if len(text.split()) < 30:
            return text
        # Truncate very long texts before passing to model
        truncated = " ".join(text.split()[:900])
        result    = self.summariser(truncated, max_length=max_length,
                                    min_length=40, do_sample=False)
        return result[0]["summary_text"]


# ─── Main Orchestrator ────────────────────────────────────────────────────────

class DocumentIntelligenceModule:
    """
    Full Module 2 pipeline.
    Input : list of file paths + dispute type from Module 1
    Output: CaseSummary (passed to Modules 3 & 4)
    """

    def __init__(self):
        self.ocr        = DocumentOCR()
        self.classifier = DocumentClassifier()
        self.gap        = GapDetector()
        self.summariser = CaseSummariser()

    def analyse_documents(
        self,
        file_paths: list[str],
        dispute_type: str,
        language:     str = "en",
        claimant:     Optional[str] = None,
        respondent:   Optional[str] = None,
    ) -> CaseSummary:

        analysed  = []
        all_text  = []
        all_types = []
        issues    = []
        amounts   = []

        for fpath in file_paths:
            print(f"[DocInt] Processing: {fpath}")
            text      = self.ocr.extract_text(fpath, language)
            doc_type, conf = self.classifier.classify(text)
            key_fields     = self.classifier.extract_key_fields(text, doc_type)

            if "amount" in key_fields:
                amounts.append(key_fields["amount"])

            doc_result = DocumentAnalysisResult(
                doc_path=fpath, doc_type=doc_type,
                confidence=conf, extracted_text=text,
                key_fields=key_fields,
            )

            # Flag low-confidence classifications
            if conf < 0.6:
                doc_result.issues.append(
                    f"Low confidence ({conf:.0%}) — manual review recommended"
                )
                doc_result.is_valid = False
                issues.append(f"{Path(fpath).name}: unclear document type")

            analysed.append(doc_result)
            all_text.append(text)
            all_types.append(doc_type)

        # Gap analysis
        gap_result = self.gap.detect_gaps(all_types, dispute_type)

        # Combine text and summarise
        combined   = "\n\n".join(all_text[:3])  # first 3 docs for summary
        summary_text = self.summariser.summarise(combined)

        # Case strength heuristic
        completeness = gap_result["completeness_pct"]
        if completeness >= 100 and not issues:
            strength = "strong"
        elif completeness >= 60:
            strength = "moderate"
        else:
            strength = "weak"

        return CaseSummary(
            dispute_type        = dispute_type,
            claimant            = claimant,
            respondent          = respondent,
            total_claim_amount  = max(amounts) if amounts else None,
            documents_submitted = gap_result["submitted"],
            missing_documents   = [m["document"] for m in gap_result["missing"]],
            flagged_issues      = issues,
            case_strength       = strength,
            summary_text        = summary_text,
        )


# ─── Synthetic data generator (for training the classifier) ──────────────────

def generate_training_dataset(output_dir: str = "./training_data", n_per_class: int = 200):
    """
    Generates synthetic labelled documents for classifier training.
    Run once before training. Saves CSV: text, label

    Requires: pip install faker reportlab
    """
    from faker import Faker
    import csv, random

    fake = Faker("en_IN")
    os_path = Path(output_dir)
    os_path.mkdir(exist_ok=True)
    rows = []

    templates = {
        "invoice": lambda: (
            f"TAX INVOICE\nInvoice No: INV-{fake.bothify('####-??')}\n"
            f"Date: {fake.date()}\nBill To: {fake.company()}\n"
            f"GSTIN: {fake.bothify('##?????####?#?Z?')}\n"
            f"Description: {fake.bs()}\nAmount: INR {random.randint(10000,500000):,}\n"
            f"Total: INR {random.randint(10000,500000):,}\nPAN: {fake.bothify('?????####?')}"
        ),
        "purchase_order": lambda: (
            f"PURCHASE ORDER\nPO No: PO-{fake.bothify('####')}\n"
            f"Date: {fake.date()}\nVendor: {fake.company()}\n"
            f"Item Description: {fake.catch_phrase()}\n"
            f"Quantity: {random.randint(1,500)} units\n"
            f"Unit Price: INR {random.randint(100,10000)}\n"
            f"Total Value: INR {random.randint(5000,250000):,}\n"
            f"Delivery Date: {fake.date()}"
        ),
        "delivery_receipt": lambda: (
            f"DELIVERY RECEIPT\nReceipt No: DR-{fake.bothify('####')}\n"
            f"Date of Delivery: {fake.date()}\nReceived from: {fake.company()}\n"
            f"Items delivered: {fake.catch_phrase()}\n"
            f"Qty Received: {random.randint(1,200)}\n"
            f"Received by: {fake.name()}\nSignature: ___"
        ),
        "contract": lambda: (
            f"SERVICE AGREEMENT\nThis agreement is entered on {fake.date()}\n"
            f"Between: {fake.company()} (Client)\nAnd: {fake.company()} (Vendor)\n"
            f"Scope of Work: {fake.paragraph()}\n"
            f"Payment Terms: Net {random.choice([30,45,60])} days\n"
            f"Contract Value: INR {random.randint(50000,2000000):,}\n"
            f"Duration: {random.randint(6,24)} months"
        ),
    }

    for label, template_fn in templates.items():
        for _ in range(n_per_class):
            rows.append({"text": template_fn(), "label": label})

    out_file = os_path / "document_classification_dataset.csv"
    with open(out_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"[DataGen] Generated {len(rows)} samples → {out_file}")
    return str(out_file)


if __name__ == "__main__":
    # Smoke test: gap detection
    gap = GapDetector()
    result = gap.detect_gaps(
        submitted_doc_types=["invoice", "delivery_receipt"],
        dispute_type="non_payment",
    )
    print("Gap analysis:", json.dumps(result, indent=2))
