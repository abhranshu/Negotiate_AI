"""
Voice upload route — Module 1.

By default this route is OFFLINE-capable: with no external API key configured
it falls back to a local path on this low-resource VM (see settings.USE_LOCAL_ASR).

POST /api/cases/{case_id}/voice  — Upload audio, extract entities, pre-fill case fields
"""
import os
import threading
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

# The whole flow below is the ACTIVE /voice implementation. (The older local-
# Whisper variant in api/routes/voice.py is not registered anywhere.)

AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}

# Deliberately small: a larger Whisper model would blow past this VM's RAM.
ASR_MODEL_SIZE = "tiny"

# The cached model is shared by every request. Whisper decoders are not
# documented as thread-safe, so transcription is serialised rather than run
# concurrently against one instance (it is CPU-bound here anyway, so parallel
# decodes would only contend).
_ASR_LOCK = threading.Lock()

# Small note: this file no longer uses the Groq API. The old Groq-dependent
# implementation was replaced with an offline-first path suitable for the
# low-resource VM.


def _load_asr_model(backend: str):
    """Load the local ASR model once per process and share it.

    load_model() reads and initialises weights from disk — seconds of work and
    hundreds of MB of RAM — and this used to happen inline on every upload.

    Raises if the backend is unavailable, so callers keep falling through to
    the next backend and then to the stub. Failures are not cached.
    """
    from api.cache import ML_MODEL_CACHE

    def _build():
        if backend == "faster_whisper":
            import faster_whisper
            return faster_whisper.load_model(ASR_MODEL_SIZE, device="cpu", compute_type="int8")
        import whisper
        return whisper.load_model(ASR_MODEL_SIZE)

    return ML_MODEL_CACHE.get_or_create(("asr", backend, ASR_MODEL_SIZE), _build, ttl=None)


def _transcribe_local(audio_path: str) -> dict:
    """
    Local offline transcription for the low-resource VM.

    Uses faster-whisper when available (lighter than openai-whisper and
    supports small quantized models). If neither ASR lib is installed, falls
    back to a demo stub so the API still accepts uploads.

    The model itself is cached process-wide (see _load_asr_model), so the
    model load is no longer part of the per-request path.
    """
    with _ASR_LOCK:
        try:
            model = _load_asr_model("faster_whisper")
            segments, info = model.transcribe(
                audio_path,
                language=None,
                beam_size=1,
                vad_filter=False,
            )
            text = " ".join(seg.text for seg in segments).strip()
            lang = info.language or "en"
            return {"text": text or "", "language": lang}
        except Exception:  # noqa: BLE001 - degrade to stub if anything fails
            pass

        try:
            model = _load_asr_model("whisper")
            result = model.transcribe(audio_path, language=None, fp16=False)
            return {
                "text": result.get("text", "").strip(),
                "language": result.get("language", "en"),
            }
        except Exception:  # noqa: BLE001
            pass

    return {
        "text": "Demo mode: no local ASR engine installed (install faster-whisper or openai-whisper for real transcription).",
        "language": "en",
    }


def _transcribe(audio_path: str) -> dict:
    """
    Choose the transcription path at runtime:
      - If a local ASR engine is requested/configured, use _transcribe_local.
      - Otherwise return the demo stub so the UI still works with no keys.

    The project no longer calls Groq for voice. The old Groq path is removed
    so a missing/bad GROQ_API_KEY cannot break this endpoint.
    """
    if not settings.USE_LOCAL_ASR:
        return {
            "text": "Demo mode: voice endpoint is running in stub mode. Set USE_LOCAL_ASR=true and install a local ASR engine (faster-whisper or openai-whisper) for real transcription.",
            "language": "en",
        }
    return _transcribe_local(audio_path)


def _run_ner(transcript: str) -> dict:
    """
    Runs entity extraction on the transcript.

    On this low-resource VM we prefer regex-only extraction so the route does
    not load a BERT model just to pull out amounts, dates, and invoices.
    The full AIML.voice_pipeline.LegalNER is used only if it is installed and
    loads successfully.
    """
    try:
        from AIML.voice_pipeline import get_legal_ner
        # Cached process-wide: LegalNER() loads a BERT pipeline, which is far
        # too expensive to rebuild on every audio upload.
        ner = get_legal_ner()
        entities = ner.extract(transcript)
        dtype, _ = ner.classify_dispute_type(transcript)
        return {"entities": entities, "dispute_type": dtype}
    except Exception as exc:  # noqa: BLE001
        # If the ML stack is not installed, fall back to regex extraction below.
        return _ner_regex_only(transcript, ner_error=str(exc))


def _ner_regex_only(transcript: str, ner_error: str | None = None) -> dict:
    """Lightweight entity extraction that does not load any model."""
    import re

    amounts = []
    for m in re.finditer(
        r"(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d{1,2})?)"
        r"|(\d[\d,]*(?:\.\d{1,2})?)\s*(?:lakhs?|crores?|rupees?)",
        transcript,
        re.IGNORECASE,
    ):
        raw = (m.group(1) or m.group(2)).replace(",", "")
        try:
            val = float(raw)
            if "lakh" in transcript.lower():
                val *= 100_000
            elif "crore" in transcript.lower():
                val *= 10_000_000
            amounts.append(val)
        except ValueError:
            pass

    dates = re.findall(
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b"
        r"|\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})\b",
        transcript,
        re.IGNORECASE,
    )
    dates = [d[0] or d[1] for d in dates if d and (d[0] or d[1])]

    invoices = re.findall(
        r"\b(?:invoice|inv|bill)#?\s*([A-Za-z0-9\-/]+)",
        transcript,
        re.IGNORECASE,
    )

    persons: list[str] = []
    orgs: list[str] = []

    dispute_type = _classify_dispute_type_regex(transcript)

    return {
        "entities": {
            "persons": persons,
            "organisations": orgs,
            "amounts": sorted(amounts, reverse=True),
            "dates": dates,
            "invoice_numbers": invoices,
        },
        "dispute_type": dispute_type,
        "ner_error": ner_error,
    }


def _classify_dispute_type_regex(transcript: str) -> str | None:
    text = transcript.lower()
    keyword_map = {
        "delayed_payment": ["delayed", "overdue", "late payment", "not paid on time", "pending payment"],
        "non_payment": ["not paid", "no payment", "unpaid", "haven't received", "did not receive payment"],
        "short_payment": ["partial", "short payment", "less amount", "deducted", "short deducted"],
        "quality_dispute": ["defective", "damaged", "poor quality", "rejected", "not as per quality"],
        "quantity_dispute": ["wrong quantity", "short supply", "missing items", "less quantity"],
        "contract_breach": ["violated", "breach", "not delivered", "cancelled", "stopped delivery"],
    }
    best = None
    best_score = 0
    for dtype, keywords in keyword_map.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best = dtype
    return best if best_score > 0 else None


def _run_voice_pipeline(audio_path: str) -> dict:
    """
    Full pipeline:
      1. Local or stub transcription → transcript + language
      2. Entity extraction (NER)
      Returns populated form fields.
    """
    result = _transcribe(audio_path)
    transcript = result["text"]
    language = result["language"]

    ner_result = _run_ner(transcript)
    entities = ner_result.get("entities", {})

    amounts = entities.get("amounts", [])
    names = entities.get("persons", []) + entities.get("organisations", [])
    dates = entities.get("dates", [])
    invoices = entities.get("invoice_numbers", [])

    return {
        "dispute_type": ner_result.get("dispute_type"),
        "claim_amount": amounts[0] if amounts else None,
        "description": transcript,
        "claimant_name": names[0] if len(names) > 0 else None,
        "respondent_name": names[1] if len(names) > 1 else None,
        "detected_language": language,
        "due_date": dates[0] if dates else None,
        "invoice_number": invoices[0] if invoices else None,
        "missing_fields": [],
        "raw_transcript": transcript,
    }


@router.post("/{case_id}/voice", response_model=CaseOut)
async def upload_voice(
    case_id:  str,
    file:     UploadFile = File(...),
    db:       Session    = Depends(get_db),
    current_user: User   = Depends(get_current_user),
):
    """Upload an audio file. Module 1 will:
      1. Transcribe locally/small-model or in demo stub mode (no Groq)
      2. Extract entities via NER (regex-first on this VM)
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

    # Persist the full extraction result (NER entities, due date, invoice ref,
    # transcript) in the case's otherwise-unused JSON column so the pipeline's
    # work isn't thrown away.
    case.doc_gap_analysis = {
        "source":            "voice",
        "claimant_name":     fields.get("claimant_name"),
        "respondent_name":   fields.get("respondent_name"),
        "due_date":          fields.get("due_date"),
        "invoice_number":    fields.get("invoice_number"),
        "detected_language": fields.get("detected_language"),
        "raw_transcript":    fields.get("raw_transcript"),
    }

    # If NER identified a respondent name, try to link an already-registered
    # user so both parties can negotiate on the case.
    if fields.get("respondent_name") and not case.respondent_id:
        match = (
            db.query(User)
            .filter(User.full_name.ilike(f"%{fields['respondent_name']}%"))
            .first()
        )
        if match:
            case.respondent_id = match.id

    db.commit()
    db.refresh(case)

    # Return the updated case (matches the CaseOut contract the web + Android
    # clients expect; the web reads r.data.description from it).
    return case
