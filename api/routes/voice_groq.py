"""
Voice upload route — Module 1 powered by Groq Whisper API.

WHY GROQ:
  - Groq runs Whisper-large-v3 on custom LPU hardware
  - Latency: ~0.3 seconds for a 30-second audio clip (vs 15-30s locally)
  - Free tier: 7,200 audio-seconds/day (enough for demo)
  - No GPU needed on your server
  - API key: https://console.groq.com (free signup)

POST /api/cases/{case_id}/voice  — Upload audio, extract entities, pre-fill case fields
"""
import os
import uuid
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from api.database import get_db
from api.models.case import Case
from api.models.user import User
from api.schemas.case import CaseOut
from api.auth import get_current_user
from api.config import settings

router = APIRouter(prefix="/api/cases", tags=["Voice"])

AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}


def _transcribe_with_groq(audio_path: str) -> dict:
    """
    Transcribes audio using Groq's Whisper-large-v3 API.
    Returns: { text, language }
    Falls back to a demo stub if GROQ_API_KEY is not set.
    """
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        # Return a demo stub so the UI still works without a key
        return {
            "text": "Demo mode: Groq API key not set. Set GROQ_API_KEY in environment.",
            "language": "en",
        }

    try:
        from groq import Groq
        client = Groq(api_key=groq_key)

        with open(audio_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), f),
                model="whisper-large-v3",
                response_format="verbose_json",   # gives us language detection too
                language=None,                    # auto-detect language
                temperature=0.0,
            )

        return {
            "text":     transcription.text,
            "language": getattr(transcription, "language", "en"),
        }
    except Exception as exc:
        raise RuntimeError(f"Groq transcription failed: {exc}")


def _run_ner(transcript: str) -> dict:
    """
    Runs the NER pipeline on English text.
    Uses the LegalNER from voice_pipeline.py (bert-base-NER + regex).
    This is fast — no Whisper model loaded here.
    """
    try:
        from AIML.voice_pipeline import LegalNER
        ner = LegalNER()
        entities = ner.extract(transcript)
        dtype, _  = ner.classify_dispute_type(transcript)
        return {
            "entities": entities,
            "dispute_type": dtype,
        }
    except Exception as exc:
        return {"entities": {}, "dispute_type": None, "ner_error": str(exc)}


def _run_voice_pipeline(audio_path: str) -> dict:
    """
    Full pipeline:
      1. Groq Whisper API → transcript + language
      2. LegalNER         → entities
      Returns populated form fields.
    """
    # Step 1: Transcribe via Groq (fast, cloud-based)
    result     = _transcribe_with_groq(audio_path)
    transcript = result["text"]
    language   = result["language"]

    # Step 2: If non-English detected, Whisper-large-v3 already translates
    # (Groq's Whisper handles this internally — no extra step needed)

    # Step 3: NER on the transcript
    ner_result = _run_ner(transcript)
    entities   = ner_result.get("entities", {})

    amounts = entities.get("amounts", [])
    names   = entities.get("persons", []) + entities.get("organisations", [])
    dates   = entities.get("dates", [])
    invoices = entities.get("invoice_numbers", [])

    return {
        "dispute_type":      ner_result.get("dispute_type"),
        "claim_amount":      amounts[0] if amounts else None,
        "description":       transcript,
        "claimant_name":     names[0] if len(names) > 0 else None,
        "respondent_name":   names[1] if len(names) > 1 else None,
        "detected_language": language,
        "due_date":          dates[0] if dates else None,
        "invoice_number":    invoices[0] if invoices else None,
        "missing_fields":    [],
        "raw_transcript":    transcript,
    }


@router.post("/{case_id}/voice")
async def upload_voice(
    case_id:  str,
    file:     UploadFile = File(...),
    db:       Session    = Depends(get_db),
    current_user: User   = Depends(get_current_user),
):
    """
    Upload an audio file. Module 1 will:
      1. Transcribe via Groq Whisper-large-v3 (sub-second)
      2. Extract entities via BERT NER
      3. Pre-populate any missing fields on the case
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.claimant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the claimant can upload voice")

    ext = os.path.splitext(file.filename or "audio.wav")[-1].lower()
    if ext not in AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format. Allowed: {AUDIO_EXTENSIONS}"
        )

    # Save uploaded file to a temp path
    raw = await file.read()
    if len(raw) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")

    audio_name = f"{uuid.uuid4()}{ext}"
    audio_path = os.path.join(settings.UPLOAD_DIR, audio_name)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(audio_path, "wb") as f:
        f.write(raw)

    # Run pipeline
    try:
        fields = _run_voice_pipeline(audio_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # Pre-fill case fields that are still empty
    if fields.get("dispute_type") and not case.dispute_type:
        case.dispute_type = fields["dispute_type"]
    if fields.get("claim_amount") and not case.claim_amount:
        case.claim_amount = fields["claim_amount"]
    if fields.get("description") and not case.description:
        case.description  = fields["description"]

    db.commit()
    db.refresh(case)

    # Return both the updated case + extracted fields
    return {
        "case_id":           case.id,
        "dispute_type":      fields.get("dispute_type"),
        "claim_amount":      fields.get("claim_amount"),
        "description":       fields.get("description"),
        "claimant_name":     fields.get("claimant_name"),
        "respondent_name":   fields.get("respondent_name"),
        "detected_language": fields.get("detected_language"),
        "due_date":          fields.get("due_date"),
        "invoice_number":    fields.get("invoice_number"),
        "raw_transcript":    fields.get("raw_transcript"),
        "missing_fields":    fields.get("missing_fields", []),
    }
