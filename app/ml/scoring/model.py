import logging
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import shap

from app.ml.scoring.features import FeatureVector, FEATURE_NAMES, FEATURE_WEIGHTS

logger = logging.getLogger("bridgescore.ml.model")

ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = ROOT / "models"
MODEL_PATH = MODELS_DIR / "model.pkl"
EXPLAINER_PATH = MODELS_DIR / "shap_explainer.pkl"
APPROVE_THRESHOLD = 65.0
CONDITIONAL_THRESHOLD = 45.0

@dataclass
class SHAPFactor:
    feature: str
    contribution: float  
    display_label: str       
    weighted_value: float 

@dataclass
class PredictionResult:
    score: float                   
    decision: str                   
    confidence_lower: float       
    confidence_upper: float        
    top_factors: list[SHAPFactor]  
    all_shap_values: dict          
    feature_vector: dict         

FEATURE_DISPLAY_LABELS = {
    "collateral_strength": "Land Collateral Strength",
    "income_regularity":   "Income Regularity",
    "income_sufficiency":  "Income Sufficiency",
    "debt_signal":         "Credit History",
    "geographic_risk":     "Geographic Risk",
}
class ScoringModel:
    
    def __init__(self):
        self._model = self._load_model()
        self._explainer = self._load_explainer()
        logger.info("ScoringModel initialized — model and explainer loaded")

    def _load_model(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. "
                "Run scripts/train_model.py first."
            )
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        logger.info(f"XGBoost model loaded from {MODEL_PATH}")
        return model

    def _load_explainer(self):
        if not EXPLAINER_PATH.exists():
            raise FileNotFoundError(
                f"SHAP explainer not found at {EXPLAINER_PATH}. "
                "Run scripts/train_model.py first."
            )
        with open(EXPLAINER_PATH, "rb") as f:
            explainer = pickle.load(f)
        logger.info(f"SHAP explainer loaded from {EXPLAINER_PATH}")
        return explainer

    def predict(self, vector: FeatureVector) -> PredictionResult:

        X = np.array([vector.to_list()], dtype=np.float32)


        raw_score = float(self._model.predict(X)[0])
        score = round(max(0.0, min(100.0, raw_score)), 2)

        if score >= APPROVE_THRESHOLD:
            decision = "Approve"
        elif score >= CONDITIONAL_THRESHOLD:
            decision = "Conditional Approve"
        else:
            decision = "Decline"


        confidence_lower = round(max(0.0, score - 5.0), 2)
        confidence_upper = round(min(100.0, score + 5.0), 2)

        shap_values = self._explainer.shap_values(X)[0]
        top_factors = self._get_top_factors(shap_values, vector)
        all_shap = {
            FEATURE_NAMES[i]: round(float(shap_values[i]), 4)
            for i in range(len(FEATURE_NAMES))
        }

        result = PredictionResult(
            score=score,
            decision=decision,
            confidence_lower=confidence_lower,
            confidence_upper=confidence_upper,
            top_factors=top_factors,
            all_shap_values=all_shap,
            feature_vector=vector.to_dict(),
        )

        logger.info(
            "Prediction complete — score=%.1f decision=%s "
            "top_factor=%s (%.3f)",
            score,
            decision,
            top_factors[0].feature if top_factors else "none",
            top_factors[0].contribution if top_factors else 0.0,
        )

        return result
    def _get_top_factors(self,shap_values: np.ndarray,vector: FeatureVector,) -> list[SHAPFactor]:

        factors = []
        feature_dict = vector.to_dict()

        for i, feature_name in enumerate(FEATURE_NAMES):
            contribution = float(shap_values[i])
            factors.append(SHAPFactor(
                feature=feature_name,
                contribution=round(contribution, 4),
                display_label=FEATURE_DISPLAY_LABELS[feature_name],
                weighted_value=round(
                    feature_dict[feature_name] * FEATURE_WEIGHTS[feature_name],
                    4
                ),
            ))

      
        factors.sort(key=lambda f: abs(f.contribution), reverse=True)
        return factors[:3]

    def predict_score_only(self, vector: FeatureVector) -> float:

        X = np.array([vector.to_list()], dtype=np.float32)
        raw = float(self._model.predict(X)[0])
        return round(max(0.0, min(100.0, raw)), 2)    

_model_instance: ScoringModel | None = None

def get_model() -> ScoringModel:
    global _model_instance
    if _model_instance is None:
        _model_instance = ScoringModel()
    return _model_instance
