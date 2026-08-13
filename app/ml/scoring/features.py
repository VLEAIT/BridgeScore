import logging
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal

from app.ml.fsv import FSVCalculator, FSVResult

logger = logging.getLogger("bridgescore.ml.features")
HUNDI_CONFIDENCE_DISCOUNT = 0.35
GULF_GAP_TOLERANCE_MONTHS = 3
NRB_MONTHLY_MULTIPLIER = 12      
NRB_LTV_RATIO = 0.60  

FEATURE_NAMES = [
    "collateral_strength",
    "income_regularity",
    "income_sufficiency",
    "debt_signal",
    "geographic_risk",
]

FEATURE_WEIGHTS = {
    "collateral_strength": 0.25,
    "income_regularity": 0.30,
    "income_sufficiency": 0.20,
    "debt_signal": 0.15,
    "geographic_risk":0.10,
}

@dataclass
class FeatureVector:
    collateral_strength:float   
    income_regularity: float  
    income_sufficiency: float  
    debt_signal:float  
    geographic_risk:float  
    hundi_applied: bool = False
    gulf_gap_applied: bool = False
    fsv_confidence: float = 1.0
    effective_monthly_income: float = 0.0

    def to_list(self) -> list[float]:
        return [
            self.collateral_strength,
            self.income_regularity,
            self.income_sufficiency,
            self.debt_signal,
            self.geographic_risk,
        ]
    def to_dict(self) -> dict[str, float]:
        return {
            "collateral_strength": self.collateral_strength,
            "income_regularity":   self.income_regularity,
            "income_sufficiency":  self.income_sufficiency,
            "debt_signal":         self.debt_signal,
            "geographic_risk":     self.geographic_risk,
        }
def _collateral_strength(fsv: float,requested_amount: float,zone: str,fsv_confidence: float,) -> float:
    if requested_amount <= 0:
        return 0.0

    ratio = fsv / requested_amount
    base = min(ratio / 2.0, 1.0)

    zone_factors = {
        "terai":    1.00,
        "hill":     0.92,
        "mountain": 0.75,
    }
    zone_factor = zone_factors.get(zone, 0.92)
    adjusted = base * zone_factor * fsv_confidence
    return round(max(0.0, min(1.0, adjusted)), 4)  

def _income_regularity(remittance_monthly: float,remittance_months_history: int,remittance_gap_months: int,hundi: bool,coop_income_monthly: float,coop_verified: bool,) -> tuple[float, bool, bool]:
    hundi_applied = False
    gulf_gap_applied = False
    if remittance_monthly == 0 or remittance_months_history == 0:
        if not coop_verified:
            return 0.30, False, False
        if coop_income_monthly >= 30000:
            return 0.72, False, False
        elif coop_income_monthly >= 15000:
            return 0.58, False, False
        elif coop_income_monthly >= 5000:
            return 0.42, False, False
        else:
            return 0.28, False, False
    if hundi:
        hundi_applied = True
        base_hundi = 1.0 - HUNDI_CONFIDENCE_DISCOUNT 
        return min(base_hundi * 0.70, 0.50), True, False

    gap_forgiven = remittance_gap_months <= GULF_GAP_TOLERANCE_MONTHS
    if remittance_gap_months > 0 and gap_forgiven:
        gulf_gap_applied = True

    if remittance_months_history >= 12 and remittance_gap_months == 0:
        score = 1.00
    elif remittance_months_history >= 12 and gulf_gap_applied:
        score = 0.90
    elif remittance_months_history >= 6 and remittance_gap_months == 0:
        score = 0.85
    elif remittance_months_history >= 6 and gulf_gap_applied:
        score = 0.78
    elif remittance_months_history >= 3 and gulf_gap_applied:
        score = 0.60
    elif remittance_months_history >= 3:
        score = 0.45 
    elif remittance_months_history >= 1:
        score = 0.32
    else:
        score = 0.20

    return round(score, 4), False, gulf_gap_applied   

def _income_sufficiency(coop_income_monthly: float,remittance_monthly: float,hundi: bool,requested_amount: float,coop_verified: bool,) -> tuple[float, float]:
    effective_remittance = (
        remittance_monthly * (1.0 - HUNDI_CONFIDENCE_DISCOUNT)
        if hundi else remittance_monthly
    )
    effective_coop = (
        coop_income_monthly * 0.80
        if not coop_verified else coop_income_monthly
    )

    total_monthly = effective_coop + effective_remittance
    twelve_x_capacity = total_monthly * NRB_MONTHLY_MULTIPLIER

    if requested_amount <= 0:
        return 0.0, total_monthly
    ratio = twelve_x_capacity / requested_amount
    score = min(ratio / 2.0, 1.0)

    return round(max(0.0, score), 4), round(total_monthly, 2)

def _debt_signal(cib_clean: bool,existing_loans_nrs: float,microfinance_member: bool,) -> float:
    if not cib_clean:
        return 0.0
    if existing_loans_nrs == 0 and not microfinance_member:
        return 1.0
    if microfinance_member and existing_loans_nrs == 0:
        return 0.88
    loan_penalty = min(existing_loans_nrs / 500_000, 0.40)
    base = 0.85 if microfinance_member else 0.80
    return round(max(0.0, base - loan_penalty), 4)    
    