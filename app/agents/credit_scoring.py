# app/agents/credit_scoring.py

import logging
import numpy as np
from app.agents.state import BridgeScoreState
from app.ml.scoring.model import get_model
from app.ml.scoring.features import FEATURE_NAMES

logger = logging.getLogger("bridgescore.agents.csa")


def csa_node(state: BridgeScoreState) -> dict:

    logger.info("CSA: Running XGBoost credit scoring")
    audit = list(state.get("audit_trail", []))
    audit.append("CSA: Running XGBoost credit scoring model...")

    feature_vector = state.get("feature_vector", {})

   
    X = np.array([[
        feature_vector.get(name, 0.0)
        for name in FEATURE_NAMES
    ]], dtype=np.float32)

    model = get_model()


    raw_score = float(model._model.predict(X)[0])
    score = round(max(0.0, min(100.0, raw_score)), 2)

    if score >= 65.0:
        recommendation = "Approve"
    elif score >= 45.0:
        recommendation = "Conditional Approve"
    else:
        recommendation = "Decline"

  
    confidence_lower = round(max(0.0, score - 5.0), 2)
    confidence_upper = round(min(100.0, score + 5.0), 2)

  
    shap_values = model._explainer.shap_values(X)[0]
    factors = []
    for i, name in enumerate(FEATURE_NAMES):
        factors.append({
            "feature":       name,
            "contribution":  round(float(shap_values[i]), 4),
            "display_label": {
                "collateral_strength": "Land Collateral Strength",
                "income_regularity":   "Income Regularity",
                "income_sufficiency":  "Income Sufficiency",
                "debt_signal":         "Credit History",
                "geographic_risk":     "Geographic Risk",
            }.get(name, name),
        })
    factors.sort(key=lambda f: abs(f["contribution"]), reverse=True)
    top_3 = factors[:3]

    all_shap = {
        FEATURE_NAMES[i]: round(float(shap_values[i]), 4)
        for i in range(len(FEATURE_NAMES))
    }

    audit.append(
        f"CSA: Score = {score}/100 [{confidence_lower}-{confidence_upper}] "
        f"→ {recommendation}"
    )
    audit.append(
        f"CSA: Top factor = {top_3[0]['display_label']} "
        f"({top_3[0]['contribution']:+.3f})"
    )

    return {
        "credit_score":      score,
        "recommendation":    recommendation,
        "confidence_lower":  confidence_lower,
        "confidence_upper":  confidence_upper,
        "top_shap_factors":  top_3,
        "all_shap_values":   all_shap,
        "audit_trail":       audit,
    }