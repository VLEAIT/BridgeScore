import json
import logging
import pickle
from pathlib import Path

import numpy as np
import xgboost as xgb
import shap
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

from app.ml.fsv import FSVCalculator
from app.ml.scoring.features import (
    engineer_features,
    FEATURE_NAMES,
    FEATURE_WEIGHTS,
)

logger = logging.getLogger("bridgescore.ml.train")

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
TRAINING_DATA_PATH = DATA_DIR / "synthetic_training_data.json"
ANCHOR_PROFILES_PATH = DATA_DIR / "synthetic_profiles.json"
MODEL_PATH = MODELS_DIR / "model.pkl"
EXPLAINER_PATH = MODELS_DIR / "shap_explainer.pkl"

XGBOOST_PARAMS = {
    "n_estimators": 300,
    "max_depth": 4,         
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 3,
    "reg_alpha": 0.1,         
    "reg_lambda": 1.0,        
    "random_state": 42,
    "n_jobs": -1,
}

def load_training_data() -> tuple[list[dict], list[float]]:
    if not TRAINING_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Training data not found at {TRAINING_DATA_PATH}. "
            "Run synthetic_data.py first."
        )

    with open(TRAINING_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    profiles = data["profiles"]
    scores = [p["expected"]["score"] for p in profiles]

    logger.info(
        f"Loaded {len(profiles)} training profiles — "
        f"score range: {min(scores):.1f} to {max(scores):.1f}"
    )
    return profiles, scores

def build_feature_matrix(profiles: list[dict],fsv_calculator: FSVCalculator,) -> np.ndarray:
    logger.info(f"Engineering features for {len(profiles)} profiles...")
    X = []
    for profile in profiles:
        vector = engineer_features(profile, fsv_calculator=fsv_calculator)
        X.append(vector.to_list())

    matrix = np.array(X, dtype=np.float32)
    logger.info(f"Feature matrix shape: {matrix.shape}")
    return matrix    

def train(X: np.ndarray,y: np.ndarray,) -> xgb.XGBRegressor:

    X_train, X_val, y_train, y_val = train_test_split(
        X, y,
        test_size=0.15,
        random_state=42,
    )

    logger.info(
        f"Train: {len(X_train)} profiles — "
        f"Val: {len(X_val)} profiles"
    )

    model = xgb.XGBRegressor(**XGBOOST_PARAMS)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    y_pred_val = model.predict(X_val)
    mae = mean_absolute_error(y_val, y_pred_val)
    r2 = r2_score(y_val, y_pred_val)

    logger.info(f"Validation MAE : {mae:.2f} points")
    logger.info(f"Validation R²  : {r2:.4f}")

    return model    

def build_shap_explainer(model: xgb.XGBRegressor,X: np.ndarray,)-> shap.TreeExplainer:

    explainer = shap.TreeExplainer(model)
    logger.info("SHAP TreeExplainer built")
    return explainer


def save_artifacts(model: xgb.XGBRegressor,explainer: shap.TreeExplainer,) -> None:
    MODELS_DIR.mkdir(exist_ok=True)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {MODEL_PATH}")

    with open(EXPLAINER_PATH, "wb") as f:
        pickle.dump(explainer, f)
    logger.info(f"SHAP explainer saved to {EXPLAINER_PATH}")    

def validate_anchor_profiles(model: xgb.XGBRegressor,fsv_calculator: FSVCalculator,) -> None:
    with open(ANCHOR_PROFILES_PATH, "r", encoding="utf-8") as f:
        anchors = json.load(f)["profiles"]

    names =    ["Ramesh", "Sita",  "Hari", "Maya", "Bir",  "Ganga"]
    expected = [71,        54,      63,     38,     84,      49]

    print("\n" + "─" * 55)
    print(f"{'Profile':<10} {'Expected':>8} {'Predicted':>9} {'Diff':>6} {'Status':>6}")
    print("─" * 55)

    all_pass = True
    for i, (name, exp) in enumerate(zip(names, expected)):
        vector = engineer_features(anchors[i], fsv_calculator=fsv_calculator)
        X = np.array([vector.to_list()], dtype=np.float32)
        pred = float(model.predict(X)[0])
        diff = pred - exp
        status = "APPROVED:" if abs(diff) <= 5 else "REJECTED"
        if abs(diff) > 5:
            all_pass = False
        print(f"{name:<10} {exp:>8} {pred:>9.1f} {diff:>+6.1f} {status:>6}")

    print("─" * 55)
    if all_pass:
        print("All anchor profiles within ±5 points APPROVED")
    else:
        print("Some profiles outside tolerance — consider recalibrating features.py REJECTED")    

def run_training_pipeline() -> None:
    """Full training pipeline — load, engineer, train, validate, save."""
    logging.basicConfig(level=logging.INFO)

    logger.info("=" * 50)
    logger.info("BridgeScore XGBoost Training Pipeline")
    logger.info("=" * 50)

    fsv_calculator = FSVCalculator()

    profiles, scores = load_training_data()
    y = np.array(scores, dtype=np.float32)

    X = build_feature_matrix(profiles, fsv_calculator)


    logger.info("Training XGBoost model...")
    model = train(X, y)

    explainer = build_shap_explainer(model, X)
    save_artifacts(model, explainer)
    validate_anchor_profiles(model, fsv_calculator)

    logger.info("Training pipeline complete")


if __name__ == "__main__":
    run_training_pipeline()