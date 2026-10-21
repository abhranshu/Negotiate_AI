"""
Document upload route — triggers Module 2 (Document Intelligence).
POST /api/cases/{case_id}/documents   — Upload one or more files
GET  /api/cases/{case_id}/documents   — List all documents for a case
"""
import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from api.database import get_db
from api.models.case import Case, Document, CASE_WITH_DOCUMENTS
from api.models.user import User
from api.schemas.case import DocumentOut
from api.auth import get_current_user
from api.config import settings

router = APIRouter(prefix="/api/cases", tags=["Documents"])

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


def _run_document_intelligence(file_path: str, dispute_type: str) -> dict:
    """
    Runs Module 2 on a single file.
    Returns a dict with: doc_type, confidence, extracted_text, key_fields, issues.

    Order: (1) OCR always (needed by every path); (2) Bedrock review when
    USE_BEDROCK=true (fast, structured JSON); (3) local DistilBERT classifier;
    (4) stub so the API still works with no ML stack.

    Heavy imports (torch, transformers, boto3) are done lazily so the API
    starts fast even on machines without a GPU or the full ML stack installed.
    """
    # OCR first — every downstream path needs the text.
    try:
        from AIML.document_intelligence import DocumentOCR

        ocr = DocumentOCR()
        text = ocr.extract_text(file_path)
    except Exception as exc:
        return {
            "doc_type":       "unknown",
            "confidence":     0.0,
            "extracted_text": "",
            "key_fields":     {},
            "issues":         [f"OCR unavailable: {exc}"],
            "is_valid":       False,
        }

    if not text or not text.strip():
        return {
            "doc_type":       "unknown",
            "confidence":     0.0,
            "extracted_text": "",
            "key_fields":     {},
            "issues":         ["No readable text extracted (blurry scan or unsupported format)"],
            "is_valid":       False,
        }

    # Bedrock review (Nova Micro) — structured classification + extraction.
    try:
        if settings.USE_BEDROCK:
            import os as _os

            from AIML.bedrock_client import review_document

            review = review_document(text, filename=_os.path.basename(file_path))
            key_fields = {
                "amount":          review.get("amount"),
                "invoice_number":  review.get("invoice_number"),
                "dates":           review.get("dates") or [],
                "parties":         review.get("parties") or [],
                "summary":         review.get("summary") or "",
            }
            # Drop nulls so the DB JSON stays clean.
            key_fields = {k: v for k, v in key_fields.items() if v not in (None, [], "")}
            conf = float(review.get("confidence") or 0.0)
            return {
                "doc_type":       review.get("doc_type") or "other",
                "confidence":     conf,
                "extracted_text": text[:4000],   # store first 4 KB
                "key_fields":     key_fields,
                "issues":         review.get("issues") or [],
                "is_valid":       bool(review.get("is_valid", conf >= 0.6)),
            }
    except Exception as exc:
        print(f"[Documents] Bedrock review failed ({exc}) — falling back to local classifier")

    try:
        from AIML.document_intelligence import get_document_classifier
        # DocumentOCR is stateless and cheap to construct; the DistilBERT
        # classifier is not — it is cached process-wide, and was previously
        # rebuilt once per uploaded file inside the loop below.
        classifier = get_document_classifier()

        doc_type, conf = classifier.classify(text)
        key_fields    = classifier.extract_key_fields(text, doc_type)

        return {
            "doc_type":       doc_type,
            "confidence":     conf,
            "extracted_text": text[:4000],   # store first 4 KB
            "key_fields":     key_fields,
            "issues":         [],
            "is_valid":       conf >= 0.6,
        }
    except Exception as exc:
        # If ML stack not installed, return stub so API still works
        return {
            "doc_type":       "unknown",
            "confidence":     0.0,
            "extracted_text": text[:4000],
            "key_fields":     {},
            "issues":         [f"ML processing unavailable: {exc}"],
            "is_valid":       False,
        }


@router.post("/{case_id}/documents", response_model=List[DocumentOut])
async def upload_documents(
    case_id:  str,
    files:    List[UploadFile] = File(...),
    db:       Session          = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    """Upload one or more documents for a case. Each file is classified by Module 2."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.claimant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the claimant can upload documents")

    # Size guard
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    results = []
    for upload in files:
        raw = await upload.read()
        if len(raw) > max_bytes:
            raise HTTPException(status_code=413, detail=f"{upload.filename} exceeds {settings.MAX_FILE_SIZE_MB} MB limit")

        # Persist file to disk
        ext       = os.path.splitext(upload.filename)[-1]
        file_name = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, file_name)
        with open(file_path, "wb") as f:
            f.write(raw)

        # Run Module 2
        m2 = _run_document_intelligence(file_path, case.dispute_type or "delayed_payment")

        doc = Document(
            id            = str(uuid.uuid4()),
            case_id       = case_id,
            filename      = upload.filename,
            file_path     = file_path,
            file_size_kb  = len(raw) // 1024,
            doc_type      = m2["doc_type"],
            confidence    = m2["confidence"],
            extracted_text= m2["extracted_text"],
            key_fields    = m2["key_fields"],
            is_valid      = m2["is_valid"],
            issues        = m2["issues"],
        )
        db.add(doc)
        results.append(doc)

    db.commit()
    for doc in results:
        db.refresh(doc)
    return results


@router.get("/{case_id}/documents", response_model=List[DocumentOut])
def list_documents(
    case_id: str,
    db:      Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all uploaded documents and their classification results for a case."""
    # Load the documents with the case rather than letting the serializer touch
    # case.documents lazily — the queries are equivalent, but this way the read
    # is explicit instead of happening during response rendering.
    case = (
        db.query(Case)
        .options(*CASE_WITH_DOCUMENTS)
        .filter(Case.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case.documents
