"""
Outcome prediction route — triggers Module 3.
POST /api/cases/{case_id}/predict  — Run XGBoost/LightGBM prediction
"""
import logging
import threading

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models.case import Case, CaseStatus, CASE_WITH_DOCUMENTS
from api.models.user import User
from api.schemas.case import PredictionOut
from api.auth import get_current_user

router = APIRouter(prefix="/api/cases", tags=["Prediction"])

logger = logging.getLogger("negotiate_ai.predict")

# Serialises the cold start only (see below). Warm requests never block on it.
_MODEL_STARTUP_LOCK = threading.Lock()


def _run_prediction(case: Case) -> dict:
    """
    Calls Module 3 OutcomePredictionEngine.
    Trains on synthetic data if no saved models exist yet.
    """
    try:
        from AIML.outcome_prediction import (
            CaseFeatures, OutcomePredictionTrainer,
            generate_synthetic_cases, models_present, get_outcome_engine,
        )
        from pathlib import Path

        model_dir = str(Path("./models"))

        # Auto-train on synthetic data if models are not present yet. Held under
        # a lock because otherwise N concurrent requests on a cold install each
        # build their own 3000-case dataset and train over each other's files.
        with _MODEL_STARTUP_LOCK:
            if not models_present(model_dir):
                print("[Predict] No saved models found — training on synthetic data...")
                df      = generate_synthetic_cases(n=3000)
                trainer = OutcomePredictionTrainer(output_dir=model_dir)
                trainer.train(df)

        # Shared engine, cached process-wide (see AIML.outcome_prediction).
        # Building one is 4 joblib.load() calls that this route used to repeat
        # on every single request. The cache key includes a fingerprint of the
        # model files, so re-training is picked up without a restart.
        engine = get_outcome_engine(model_dir=model_dir)

        features = CaseFeatures(
            claim_amount_inr         = case.claim_amount or 100_000,
            overdue_days             = case.overdue_days or 60,
            previous_payments_made   = False,
            invoice_count            = len(case.documents),
            documentation_score      = _doc_score(case),
            has_signed_contract      = _has_doc_type(case, "contract"),
            has_delivery_proof       = _has_doc_type(case, "delivery_receipt"),
            claimant_enterprise_size = "micro",
            respondent_size          = "medium",
            prior_disputes           = 0,
            industry                 = case.industry or "other",
            dispute_type             = case.dispute_type.value if case.dispute_type else "delayed_payment",
            state                    = case.state or "other",
            msefc_filing             = False,
            days_since_dispute       = case.overdue_days or 60,
        )
        report = engine.predict(features)
        result = {
            "settlement_probability":  report.settlement_probability,
            "settlement_range_low":    report.settlement_range_low,
            "settlement_range_high":   report.settlement_range_high,
            "adjudication_days":       report.adjudication_days,
            "confidence_band":         report.confidence_band,
            "key_factors":             report.key_factors,
            "recommendation":          report.recommendation,
            "is_fallback":             False,
        }

        # Bedrock explainer — grounds the ML numbers in the uploaded docs.
        # ML stays the source of truth for numbers; Bedrock only enriches the
        # recommendation text (never overrides probabilities/ranges).
        try:
            from api.config import settings as _settings

            if bool(getattr(_settings, "USE_BEDROCK", False)):
                from AIML.bedrock_client import converse as _bedrock_converse

                doc_bits = [
                    (d.extracted_text or "")[:1200]
                    for d in (case.documents or [])
                    if d.extracted_text
                ]
                doc_context = "\n---\n".join(doc_bits[:3]) or "No documents uploaded."
                bedrock_rec = _bedrock_converse(
                    f"MSME dispute: claim Rs.{case.claim_amount or 0:,.0f}, "
                    f"{case.overdue_days or 0} days overdue, "
                    f"dispute type {case.dispute_type}, industry {case.industry}.\n"
                    f"ML model output: settlement probability "
                    f"{report.settlement_probability:.0%}, range "
                    f"Rs.{report.settlement_range_low:,.0f}-Rs.{report.settlement_range_high:,.0f}, "
                    f"adjudication ~{report.adjudication_days} days.\n\n"
                    f"Uploaded document extracts:\n{doc_context}\n\n"
                    "In 3 short bullets: (1) do the documents strengthen or weaken "
                    "the claim, (2) adjusted settlement guidance, "
                    "(3) one next step. Then one line: adjusted range or 'Range stands'.",
                    system=(
                        "You are an MSME settlement adviser under the MSMED Act 2006. "
                        "The ML numbers are authoritative — reason about them using "
                        "the document extracts, do not invent different numbers."
                    ),
                    model=_settings.BEDROCK_MEDIATOR_MODEL,
                    max_tokens=350,
                    temperature=0.2,
                )
                result["recommendation"] = (
                    f"{report.recommendation}\n\n--- Bedrock document review ---\n{bedrock_rec}"
                )
        except Exception as e:
            logger.warning("Bedrock prediction explainer failed, keeping ML text: %s", e)

        return result
    except Exception as exc:
        # Module 3 is unavailable. Rather than silently presenting a hardcoded
        # number as if the model produced it, we return a clearly-labelled
        # fallback estimate and log loudly. Clients must check `is_fallback`.
        logger.warning("Module 3 ML engine unavailable, returning labelled fallback: %s", exc)
        return {
            "settlement_probability":  0.65,
            "settlement_range_low":    (case.claim_amount or 100_000) * 0.6,
            "settlement_range_high":   (case.claim_amount or 100_000) * 0.9,
            "adjudication_days":       180,
            "confidence_band":         "low",
            "key_factors":             [],
            "recommendation":          f"[FALLBACK — ML UNAVAILABLE] ML engine not available ({exc}). This is a default estimate, not a model prediction.",
            "is_fallback":             True,
        }


def _doc_score(case: Case) -> float:
    """Compute documentation completeness score (0-1) from uploaded docs."""
    if not case.documents:
        return 0.0
    valid = sum(1 for d in case.documents if d.is_valid)
    return valid / len(case.documents)


def _has_doc_type(case: Case, doc_type: str) -> bool:
    return any(d.doc_type == doc_type for d in case.documents)


@router.post("/{case_id}/predict", response_model=PredictionOut)
def predict_outcome(
    case_id:      str,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """
    Run Module 3 outcome prediction on a case.
    Automatically trains on synthetic data if models are not saved yet.
    """
    # The feature vector is built from case.documents (count, validity, doc
    # types), so load them with the case instead of letting a lazy SELECT fire
    # in the middle of the feature build.
    case = (
        db.query(Case)
        .options(*CASE_WITH_DOCUMENTS)
        .filter(Case.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.claimant_id != current_user.id and case.respondent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")

    result = _run_prediction(case)

    # Persist Module 3 outputs to the Case row
    case.settlement_probability     = result["settlement_probability"]
    case.settlement_range_low       = result["settlement_range_low"]
    case.settlement_range_high      = result["settlement_range_high"]
    case.adjudication_days          = result["adjudication_days"]
    case.prediction_confidence      = result["confidence_band"]
    case.prediction_recommendation  = result["recommendation"]
    if case.status == CaseStatus.draft:
        case.status = CaseStatus.submitted
    db.commit()

    return result
