"""
Outcome prediction route — triggers Module 3.
POST /api/cases/{case_id}/predict  — Run XGBoost/LightGBM prediction
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models.case import Case, CaseStatus
from api.models.user import User
from api.schemas.case import PredictionOut
from api.auth import get_current_user

router = APIRouter(prefix="/api/cases", tags=["Prediction"])


def _run_prediction(case: Case) -> dict:
    """
    Calls Module 3 OutcomePredictionEngine.
    Trains on synthetic data if no saved models exist yet.
    """
    try:
        from outcome_prediction import (
            CaseFeatures, OutcomePredictionTrainer,
            OutcomePredictionEngine, generate_synthetic_cases
        )
        from pathlib import Path

        model_dir = Path("./models")

        # Auto-train on synthetic data if models not present yet
        if not (model_dir / "settlement_classifier.pkl").exists():
            print("[Predict] No saved models found — training on synthetic data...")
            df      = generate_synthetic_cases(n=3000)
            trainer = OutcomePredictionTrainer(output_dir=str(model_dir))
            trainer.train(df)

        engine = OutcomePredictionEngine(model_dir=str(model_dir))

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
        return {
            "settlement_probability":  report.settlement_probability,
            "settlement_range_low":    report.settlement_range_low,
            "settlement_range_high":   report.settlement_range_high,
            "adjudication_days":       report.adjudication_days,
            "confidence_band":         report.confidence_band,
            "key_factors":             report.key_factors,
            "recommendation":          report.recommendation,
        }
    except Exception as exc:
        # Stub response so the API remains usable without full ML stack
        return {
            "settlement_probability":  0.65,
            "settlement_range_low":    (case.claim_amount or 100_000) * 0.6,
            "settlement_range_high":   (case.claim_amount or 100_000) * 0.9,
            "adjudication_days":       180,
            "confidence_band":         "low",
            "key_factors":             [],
            "recommendation":          f"ML engine not available ({exc}). Default estimate shown.",
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
    case = db.query(Case).filter(Case.id == case_id).first()
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
