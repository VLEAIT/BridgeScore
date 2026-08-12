import json
import logging
import random
from decimal import decimal
from pathlib import Path
from typinh import Any


from app.ml.fsv import FSVCalculator

logger =logging.getLogger("bridgescore.ml.synthetic_data")

ROOT=Path(__file__).resolve().parents[3]
DATA_DIR=ROOT / "data"
ANCHOR_PROFILES_PATH=DATA_DIR / "synthetic_profiles.json"
OUTPUT_PATH=DATA_DIR / "synthetic_training_data.json"
WEIGHTS={
    "collateral_strength":0.25,
    "income_regularity":0.30,
    "income_sufficienct":0.20,
    "debt_signal":0.15,
    "geographic_risk":0.10,   
}

HUNDI_CONFIDENCE_DISCOUNT=0.35
GULF_GAP_TOLERANCE_MONTHS=3
NRB_MONTHLY_INCOME_MULTIPLIER=12
ZONE_BASE_SCORES={
    "terai":1.0,
    "hill":0.65,
    "mountain":0.30,
}
LAND_TYPE_BONUS={
    "Khet":0.10,
    "Bari":0.00,
    "Gharbari":-0.05,
}

GRADE_QUALITIY={
    "Aabal":1.0,
    "Doyam":0.75,
    "Sim":0.50,
    "Chahar":0.30,
}
def score_collateral_strength(fsv:float,requested_amount:float,zone:str)->float:
    if requested_amount <= 0:
        return 0.0
    ratio=fsv/requested_amount
    base=min(ratio/2.0,1.0)    
    zone_discount={"terai":0.0,"hill":0.05,"mountain":0.15}
    return max(0.0, round(base - zone_discount.get(zone,0.05),4))


def score_income_regularity(
    remittance_monthly:float,
)    
