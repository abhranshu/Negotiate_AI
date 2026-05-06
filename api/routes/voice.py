"""
Voice upload route — triggers Module 1 (Voice Pipeline).
POST /api/cases/{case_id}/voice  — Upload audio, extract entities, pre-fill case fields
"""
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from api.database import get_db
from api.models.case import Case
from api.models.user import User
from api.schemas.case import CaseOut
from api.auth import get_current_user
from api.config import settings

router = APIRouter(prefix="/api/cases", tags=["Voice"])

AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}


def _run_voice_pipeline(audio_path: str) -> dict:
    """
    Runs Module 1 on the uploaded audio file.
    Returns populated form fields as a dict.
    Falls back to empty dict if ML stack not installed.
    """
    try:
        from voice_pipeline import VoiceToFormPipeline
        pipeline = VoiceToFormPipeline(whisper_size="base")   # use "base" for speed; change to "medium" in prod
        form     = pipeline.process(audio_path)
        return {
            "dispute_type":    form.dispute_type,
            "claim_amount":    form.invoice_amount,
            "description":     form.description,
            "claimant_name":   form.claimant_name,
            "respondent_name": form.respondent_name,
            "detected_language": form.detected_language,
            "missing_fields":  form.missing_fields,
        }
    except Exception as exc:
        return {"error": str(exc)}


@router.post("/{case_id}/voice", response_model=CaseOut)
async def upload_voice(
    case_id:  str,
    file:     UploadFile = File(...),
    db:       Session    = Depends(get_db),
    current_user: User   = Depends(get_current_user),
):
    """
    Upload an audio file. Module 1 will transcribe, translate, extract entities,
    and pre-populate any missing fields on the case.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.claimant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the claimant can upload voice")

    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported audio format. Allowed: {AUDIO_EXTENSIONS}")

    # Save audio file
    audio_name = f"{uuid.uuid4()}{ext}"
    audio_path = os.path.join(settings.UPLOAD_DIR, audio_name)
    raw = await file.read()
    with open(audio_path, "wb") as f:
        f.write(raw)

    # Run Module 1
    fields = _run_voice_pipeline(audio_path)

    # Pre-fill case fields that are still empty
    if fields.get("dispute_type") and not case.dispute_type:
        case.dispute_type = fields["dispute_type"]
    if fields.get("claim_amount") and not case.claim_amount:
        case.claim_amount = fields["claim_amount"]
    if fields.get("description") and not case.description:
        case.description  = fields["description"]

    db.commit()
    db.refresh(case)
    return case
