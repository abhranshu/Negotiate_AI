"""
Module 3 — Outcome Prediction Engine
=====================================
Predicts three things per case:
  1. P(out-of-court settlement)           → float [0,1]
  2. Likely settlement range              → (low_INR, high_INR)
  3. Estimated adjudication timeline      → int (days, if negotiation fails)

Model: XGBoost (primary) + LightGBM (ensemble member)
Input: Structured features from Modules 1 & 2
Output: PredictionReport dataclass

─── Data sources ────────────────────────────────────────────────────────────
Primary (apply via RTI or MOU):
  - MSEFC case database via MSME Ministry RTI (Section 6, RTI Act 2005)
    RTI portal: https://rtionline.gov.in
    Ask for: anonymised case outcomes, amounts, industry, state, duration

  - MSME Samadhan portal public data: https://samadhaan.msme.gov.in
    (aggregated statistics — limited but publicly accessible)

Secondary / proxy datasets:
  - eCourts case data (Indian judiciary):  https://ecourts.gov.in/ecourts_home
  - NCLT / NCLAT insolvency case outcomes: https://nclt.gov.in
  - World Bank Doing Business India data:  https://data.worldbank.org
  - SIDBI MSME Pulse reports:             https://www.sidbi.in/en/publications

Synthetic fallback (when real data is scarce):
  - Use generate_synthetic_cases() below to create labelled training data
    based on MSMED Act rules and MSEFC published statistics
"""

import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import xgboost as xgb
import lightgbm as lgb
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import roc_auc_score, mean_absolute_error
from sklearn.calibration import CalibratedClassifierCV
import shap


# ─── Data schema ─────────────────────────────────────────────────────────────

INDUSTRIES = [
    "textiles", "food_processing", "chemicals", "engineering",
    "pharmaceuticals", "auto_components", "electronics", "construction",
    "services", "other",
]

STATES = [
    "MH", "DL", "GJ", "KA", "TN", "UP", "WB", "RJ",
    "HR", "MP", "TG", "AP", "other",
]


@dataclass
class CaseFeatures:
    """Input features for the prediction model."""
    # Financial
    claim_amount_inr:        float
    overdue_days:            int
    previous_payments_made:  bool   # has buyer made partial payments before?
    invoice_count:           int    # number of invoices in dispute

    # Documentation
    documentation_score:     float  # 0–1 from Module 2 completeness_pct / 100
    has_signed_contract:     bool
    has_delivery_proof:      bool

    # Parties
    claimant_enterprise_size: str   # "micro" | "small" | "medium"
    respondent_size:          str   # "micro" | "small" | "medium" | "large"
    prior_disputes:           int   # number of prior cases between same parties
    industry:                 str   # from INDUSTRIES list

    # Dispute
    dispute_type:             str   # from DISPUTE_TYPES
    state:                    str   # MSEFC jurisdiction state code

    # Procedural
    msefc_filing:             bool  # already filed at MSEFC?
    days_since_dispute:       int

    # Derived (computed automatically)
    amount_log:               float = 0.0
    overdue_ratio:            float = 0.0   # overdue_days / 30
    doc_amount_interaction:   float = 0.0

    def compute_derived(self):
        self.amount_log             = np.log1p(self.claim_amount_inr)
        self.overdue_ratio          = self.overdue_days / 30.0
        self.doc_amount_interaction = self.documentation_score * self.amount_log


@dataclass
class PredictionReport:
    settlement_probability:  float           # P(out-of-court settlement)
    settlement_range_low:    float           # INR
    settlement_range_high:   float           # INR
    adjudication_days:       int             # if negotiation fails
    confidence_band:         str             # "high" | "medium" | "low"
    key_factors:             list[dict]      # SHAP-based explanations
    recommendation:          str


# ─── Feature engineering ─────────────────────────────────────────────────────

class FeatureEngineer:
    ENTERPRISE_MAP = {"micro": 0, "small": 1, "medium": 2, "large": 3}

    def __init__(self):
        self.le_industry     = LabelEncoder().fit(INDUSTRIES)
        self.le_state        = LabelEncoder().fit(STATES)
        self.le_dispute      = LabelEncoder().fit([
            "delayed_payment", "non_payment", "short_payment",
            "quality_dispute", "quantity_dispute", "contract_breach"
        ])
        self.scaler = StandardScaler()

    def to_array(self, features: CaseFeatures) -> np.ndarray:
        features.compute_derived()

        industry = (self.le_industry.transform([features.industry])[0]
                    if features.industry in self.le_industry.classes_ else 0)
        state    = (self.le_state.transform([features.state])[0]
                    if features.state in self.le_state.classes_ else 0)
        dispute  = (self.le_dispute.transform([features.dispute_type])[0]
                    if features.dispute_type in self.le_dispute.classes_ else 0)

        return np.array([
            features.claim_amount_inr,
            features.amount_log,
            features.overdue_days,
            features.overdue_ratio,
            float(features.previous_payments_made),
            features.invoice_count,
            features.documentation_score,
            float(features.has_signed_contract),
            float(features.has_delivery_proof),
            self.ENTERPRISE_MAP.get(features.claimant_enterprise_size, 0),
            self.ENTERPRISE_MAP.get(features.respondent_size, 0),
            features.prior_disputes,
            industry,
            dispute,
            state,
            float(features.msefc_filing),
            features.days_since_dispute,
            features.doc_amount_interaction,
        ], dtype=np.float32)

    FEATURE_NAMES = [
        "claim_amount_inr", "amount_log", "overdue_days", "overdue_ratio",
        "previous_payments_made", "invoice_count", "documentation_score",
        "has_signed_contract", "has_delivery_proof",
        "claimant_size", "respondent_size", "prior_disputes",
        "industry", "dispute_type", "state", "msefc_filing",
        "days_since_dispute", "doc_amount_interaction",
    ]


# ─── Synthetic data generator ─────────────────────────────────────────────────

def generate_synthetic_cases(n: int = 5000, seed: int = 42) -> pd.DataFrame:
    """
    Generates synthetic MSEFC-style case data for model bootstrapping.
    Outcome rules are derived from MSMED Act + published MSEFC statistics.

    Replace with real MSEFC data as soon as it becomes available.
    """
    rng = np.random.default_rng(seed)
    rows = []

    for _ in range(n):
        claim      = rng.lognormal(mean=12.5, sigma=1.5)  # ~INR 2.7L median
        overdue    = int(rng.exponential(90))
        doc_score  = rng.beta(4, 2)
        has_cont   = rng.random() > 0.45
        has_deliv  = rng.random() > 0.35
        prior      = int(rng.poisson(0.4))
        cl_size    = rng.choice(["micro","small","medium"], p=[0.55,0.30,0.15])
        re_size    = rng.choice(["small","medium","large"], p=[0.30,0.45,0.25])
        dtype      = rng.choice(["delayed_payment","non_payment","short_payment",
                                  "quality_dispute","quantity_dispute","contract_breach"],
                                 p=[0.35,0.25,0.15,0.10,0.10,0.05])
        industry   = rng.choice(INDUSTRIES)
        state      = rng.choice(STATES)
        msefc      = rng.random() > 0.6
        days_old   = int(rng.exponential(60))

        # Settlement probability model (based on domain knowledge)
        p_settle = (
            0.55
            + 0.20 * doc_score
            + 0.10 * float(has_cont)
            + 0.08 * float(has_deliv)
            + 0.05 * (1 if re_size == "large" else 0)
            - 0.10 * (overdue / 365)
            - 0.05 * float(dtype == "non_payment")
            + 0.03 * min(prior, 3) * (-1)
        )
        p_settle = float(np.clip(p_settle + rng.normal(0, 0.08), 0.05, 0.95))
        settled   = int(rng.random() < p_settle)

        # Settlement amount (% of claim)
        pct = rng.beta(7, 3) if settled else np.nan
        settlement_amount = float(claim * pct) if settled else np.nan

        # Adjudication duration (days, if not settled)
        adj_days = int(rng.gamma(shape=4, scale=45)) + 60 if not settled else None

        rows.append({
            "claim_amount_inr":        round(claim, 2),
            "overdue_days":            overdue,
            "previous_payments_made":  int(rng.random() > 0.5),
            "invoice_count":           int(rng.poisson(1.8) + 1),
            "documentation_score":     round(doc_score, 3),
            "has_signed_contract":     int(has_cont),
            "has_delivery_proof":      int(has_deliv),
            "claimant_enterprise_size": cl_size,
            "respondent_size":         re_size,
            "prior_disputes":          prior,
            "industry":                industry,
            "dispute_type":            dtype,
            "state":                   state,
            "msefc_filing":            int(msefc),
            "days_since_dispute":      days_old,
            # Targets
            "settled":                 settled,
            "settlement_pct":          round(float(pct), 3) if settled else None,
            "adjudication_days":       adj_days,
        })

    return pd.DataFrame(rows)


# ─── Model training ───────────────────────────────────────────────────────────

class OutcomePredictionTrainer:

    def __init__(self, output_dir: str = "./models"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.fe = FeatureEngineer()

    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Convert DataFrame rows to feature matrix."""
        rows = []
        for _, row in df.iterrows():
            cf = CaseFeatures(
                claim_amount_inr        = row["claim_amount_inr"],
                overdue_days            = row["overdue_days"],
                previous_payments_made  = bool(row["previous_payments_made"]),
                invoice_count           = row["invoice_count"],
                documentation_score     = row["documentation_score"],
                has_signed_contract     = bool(row["has_signed_contract"]),
                has_delivery_proof      = bool(row["has_delivery_proof"]),
                claimant_enterprise_size= row["claimant_enterprise_size"],
                respondent_size         = row["respondent_size"],
                prior_disputes          = row["prior_disputes"],
                industry                = row["industry"],
                dispute_type            = row["dispute_type"],
                state                   = row["state"],
                msefc_filing            = bool(row["msefc_filing"]),
                days_since_dispute      = row["days_since_dispute"],
            )
            rows.append(self.fe.to_array(cf))
        return np.vstack(rows)

    def train(self, df: pd.DataFrame):
        print(f"[Train] Dataset: {len(df)} cases, settled={df['settled'].mean():.1%}")
        X = self.prepare_features(df)
        y = df["settled"].values

        # ── Classifier: settlement probability ──
        xgb_clf = xgb.XGBClassifier(
            n_estimators       = 400,
            max_depth          = 5,
            learning_rate      = 0.05,
            subsample          = 0.8,
            colsample_bytree   = 0.8,
            scale_pos_weight   = (y == 0).sum() / (y == 1).sum(),
            eval_metric        = "auc",
            use_label_encoder  = False,
            random_state       = 42,
            n_jobs             = -1,
        )
        # Calibrate probabilities (Platt scaling)
        calibrated_clf = CalibratedClassifierCV(xgb_clf, cv=5, method="sigmoid")
        calibrated_clf.fit(X, y)

        cv_auc = cross_val_score(xgb_clf, X, y, cv=5, scoring="roc_auc")
        print(f"[Train] Settlement AUC: {cv_auc.mean():.3f} ± {cv_auc.std():.3f}")

        # ── Regressor: settlement percentage (on settled cases only) ──
        settled_mask = df["settled"] == 1
        X_settled    = X[settled_mask]
        y_pct        = df.loc[settled_mask, "settlement_pct"].values

        lgb_reg = lgb.LGBMRegressor(
            n_estimators  = 300,
            max_depth     = 4,
            learning_rate = 0.05,
            num_leaves    = 31,
            random_state  = 42,
        )
        lgb_reg.fit(X_settled, y_pct)
        pct_pred = lgb_reg.predict(X_settled)
        print(f"[Train] Settlement % MAE: {mean_absolute_error(y_pct, pct_pred):.3f}")

        # ── Regressor: adjudication days (on unsettled cases) ──
        unsettled_mask = df["settled"] == 0
        X_unsettled    = X[unsettled_mask]
        y_days         = df.loc[unsettled_mask, "adjudication_days"].values.astype(float)

        lgb_days = lgb.LGBMRegressor(
            n_estimators  = 300,
            max_depth     = 4,
            learning_rate = 0.05,
            num_leaves    = 31,
            random_state  = 42,
        )
        lgb_days.fit(X_unsettled, y_days)

        # Save models
        joblib.dump(calibrated_clf, self.output_dir / "settlement_classifier.pkl")
        joblib.dump(lgb_reg,        self.output_dir / "settlement_pct_regressor.pkl")
        joblib.dump(lgb_days,       self.output_dir / "adjudication_days_regressor.pkl")
        joblib.dump(self.fe,        self.output_dir / "feature_engineer.pkl")
        print(f"[Train] Models saved to {self.output_dir}/")

        return calibrated_clf, lgb_reg, lgb_days


# ─── Inference ────────────────────────────────────────────────────────────────

class OutcomePredictionEngine:

    def __init__(self, model_dir: str = "./models"):
        model_dir = Path(model_dir)
        self.clf      = joblib.load(model_dir / "settlement_classifier.pkl")
        self.pct_reg  = joblib.load(model_dir / "settlement_pct_regressor.pkl")
        self.days_reg = joblib.load(model_dir / "adjudication_days_regressor.pkl")
        self.fe       = joblib.load(model_dir / "feature_engineer.pkl")

    def predict(self, features: CaseFeatures) -> PredictionReport:
        x = self.fe.to_array(features).reshape(1, -1)

        # Settlement probability
        p_settle = float(self.clf.predict_proba(x)[0][1])

        # Settlement range (predict % then apply to claim amount)
        pct_mid   = float(np.clip(self.pct_reg.predict(x)[0], 0.3, 1.0))
        pct_low   = max(pct_mid - 0.10, 0.25)
        pct_high  = min(pct_mid + 0.10, 1.00)
        range_low  = features.claim_amount_inr * pct_low
        range_high = features.claim_amount_inr * pct_high

        # Adjudication days
        adj_days = max(int(self.days_reg.predict(x)[0]), 30)

        # Confidence band from model calibration spread
        if p_settle > 0.72 or p_settle < 0.28:
            band = "high"
        elif p_settle > 0.60 or p_settle < 0.40:
            band = "medium"
        else:
            band = "low"

        # SHAP explanations (top 5 factors)
        key_factors = self._shap_factors(x, features)

        # Recommendation
        if p_settle >= 0.65:
            rec = (f"Strong settlement outlook ({p_settle:.0%}). "
                   f"Suggested range: ₹{range_low:,.0f}–₹{range_high:,.0f}. "
                   f"Proceed to negotiation.")
        elif p_settle >= 0.40:
            rec = (f"Moderate settlement chance ({p_settle:.0%}). "
                   f"Strengthen documentation before negotiation. "
                   f"If negotiation fails, expect adjudication in ~{adj_days} days.")
        else:
            rec = (f"Low settlement probability ({p_settle:.0%}). "
                   f"Consider direct MSEFC filing. "
                   f"Expected adjudication: ~{adj_days} days.")

        return PredictionReport(
            settlement_probability  = round(p_settle, 3),
            settlement_range_low    = round(range_low, 2),
            settlement_range_high   = round(range_high, 2),
            adjudication_days       = adj_days,
            confidence_band         = band,
            key_factors             = key_factors,
            recommendation          = rec,
        )

    def _shap_factors(self, x: np.ndarray, features: CaseFeatures) -> list[dict]:
        """Compute SHAP values for interpretability."""
        try:
            # XGBoost inner estimator for SHAP
            inner_model = self.clf.calibrated_classifiers_[0].estimator
            explainer   = shap.TreeExplainer(inner_model)
            shap_vals   = explainer.shap_values(x)[0]

            names = self.fe.FEATURE_NAMES
            pairs = sorted(zip(names, shap_vals), key=lambda t: abs(t[1]), reverse=True)
            return [
                {
                    "factor":    name,
                    "impact":    round(float(val), 4),
                    "direction": "positive" if val > 0 else "negative",
                }
                for name, val in pairs[:5]
            ]
        except Exception:
            return []


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 1. Generate synthetic data
    print("Generating synthetic training data...")
    df = generate_synthetic_cases(n=5000)
    print(df.describe())

    # 2. Train
    trainer = OutcomePredictionTrainer(output_dir="./models")
    trainer.train(df)

    # 3. Test inference
    engine = OutcomePredictionEngine(model_dir="./models")
    test_case = CaseFeatures(
        claim_amount_inr        = 450_000,
        overdue_days            = 120,
        previous_payments_made  = True,
        invoice_count           = 3,
        documentation_score     = 0.85,
        has_signed_contract     = True,
        has_delivery_proof      = True,
        claimant_enterprise_size= "micro",
        respondent_size         = "large",
        prior_disputes          = 0,
        industry                = "textiles",
        dispute_type            = "delayed_payment",
        state                   = "MH",
        msefc_filing            = False,
        days_since_dispute      = 45,
    )
    report = engine.predict(test_case)
    print("\n=== Prediction Report ===")
    print(f"Settlement probability : {report.settlement_probability:.1%}")
    print(f"Settlement range       : ₹{report.settlement_range_low:,.0f} – ₹{report.settlement_range_high:,.0f}")
    print(f"Adjudication timeline  : ~{report.adjudication_days} days")
    print(f"Confidence             : {report.confidence_band}")
    print(f"Recommendation         : {report.recommendation}")
    print(f"Key factors            : {json.dumps(report.key_factors, indent=2)}")
