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


def score_income_regularity(remittance_monthly:float,remittance_months_history:int,remittacne_gap_months:int,hundi:bool,coop_income_monthly:flaot,)->float:
    if remittance_monthly ==0:
        if coop_income_monthly>=30000:
            return 0.70
        elif coop_income_monthly >= 15000:
            return 0.50
        else:
            return 0.30
    if hundi:
        return HUNDI_CONFIDENCE_DISCOUNT +0.10
    gap_forgiven =remittance_gap_monthly <= GULF_GAP_TOLERANCE_MONTHS
    if  remittance_months_history >= 12  and remittance_gap_months==0:
        return 1.0
    elif remittance_months_history >=6 and gap_forgiven:
        return 0.80
    elif remittance_months_history>=3 and gap_forgiven:
        return 0.60
    elif remittance_months_history >=1:
        return 0.40
    else:
        return 0.20
                        


