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
def _collateral_strength(
    fsv: float,
    requested_amount: float,
    zone: str,
    fsv_confidence: float,
) -> float:
    # If no valid requested amount or no collateral valuation, strength is 0
    if requested_amount <= 0 or fsv <= 0:
        return 0.0

    fsv_max_loan = fsv * NRB_LTV_RATIO

    # Prevent division by zero if NRB_LTV_RATIO is 0 or fsv_max_loan is invalid
    if fsv_max_loan <= 0:
        return 0.0

    ratio = fsv / requested_amount
    base = min(ratio / 2.0, 1.0)

    if requested_amount > fsv_max_loan:
        overage_ratio = requested_amount / fsv_max_loan
        base = base / overage_ratio

    zone_factors = {
        "terai": 1.00,
        "hill": 0.92,
        "mountain": 0.75,
    }
    zone_factor = zone_factors.get(zone.lower(), 0.92)
    adjusted = base * zone_factor * fsv_confidence

    return round(max(0.0, min(1.0, adjusted)), 4) 

def _income_regularity(remittance_monthly: float,remittance_months_history: int,remittance_gap_months: int,hundi: bool,coop_income_monthly: float,coop_verified: bool,hundi_proxy_count:int=0) -> tuple[float, bool, bool]:
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
        proxy_bonus = min(hundi_proxy_count * 0.05, 0.15)
        return round(min(base_hundi * 0.70 + proxy_bonus, 0.60), 4), True, False

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
        score = 0.69
    elif remittance_months_history >= 3 and gulf_gap_applied:
        score = 0.60
    elif remittance_months_history >= 3:
        score = 0.45 
    elif remittance_months_history >= 1:
        score = 0.32
    else:
        score = 0.20

    return round(score, 4), False, gulf_gap_applied   

def _income_sufficiency(coop_income_monthly: float,remittance_monthly: float,hundi: bool,requested_amount: float,coop_verified: bool,regularity_score:float) -> tuple[float, float]:
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
    score = min(ratio / 2.5, 1.0)
    adjusted=score*regularity_score

    return round(max(0.0, adjusted), 4), round(total_monthly, 2)

def _debt_signal(cib_clean: bool,existing_loans_nrs: float,microfinance_member: bool,) -> float:
    if not cib_clean:
        return 0.0
    if existing_loans_nrs == 0 and not microfinance_member:
        return 0.75
    if microfinance_member and existing_loans_nrs == 0:
        return 0.88
    loan_penalty = min(existing_loans_nrs / 500_000, 0.40)
    base = 0.85 if microfinance_member else 0.80
    return round(max(0.0, base - loan_penalty), 4)    

def _geographic_risk(zone: str,land_type: str,land_grade: str,) -> float:
    zone_scores = {
        "terai":    0.88,
        "hill":     0.62,
        "mountain": 0.32,
    }

    land_type_adjustments = {
        "Khet":     +0.10,
        "Bari":     +0.00,
        "Gharbari": -0.08,
    }

    land_grade_adjustments = {
        "Aabal":  +0.05,
        "Doyam":  +0.00,
        "Sim":    -0.05,
        "Chahar": -0.10,
    }

    base = zone_scores.get(zone, 0.62)
    land_adj = land_type_adjustments.get(land_type, 0.0)
    grade_adj = land_grade_adjustments.get(land_grade, 0.0)

    return round(max(0.0, min(1.0, base + land_adj + grade_adj)), 4)

def engineer_features(profile: dict,fsv_result: Optional[FSVResult] = None,fsv_calculator: Optional[FSVCalculator] = None,) -> FeatureVector:
    land = profile["land"]
    income = profile["income"]
    credit = profile["credit"]
    application = profile["application"]
    zone = profile.get("zone", "hill")
    if fsv_result is None:
        if fsv_calculator is None:
            fsv_calculator = FSVCalculator()
        fsv_result = fsv_calculator.calculate(
            district=profile["district"],
            land_grade=land["land_grade"],
            land_area_hectares=land["land_area_hectares"],
            sarkaari_mool=Decimal(str(land["sarkaari_mool_nrs"])),
            malpot_verified=land["malpot_verified"],
        )

    fsv = float(fsv_result.fsv)
    requested = float(application["requested_amount_nrs"])
    collateral = _collateral_strength(
        fsv=fsv,
        requested_amount=requested,
        zone=zone,
        fsv_confidence=fsv_result.confidence,
    )

    regularity, hundi_applied, gulf_gap_applied = _income_regularity(
        remittance_monthly=income["remittance_monthly_nrs"],
        remittance_months_history=income["remittance_months_history"],
        remittance_gap_months=income["remittance_gap_months"],
        hundi=income["hundi"],
        coop_income_monthly=income["coop_income_monthly_nrs"],
        coop_verified=income["coop_verified"],
        hundi_proxy_count=len(income.get("hundi_proxy_signals", [])),
)
    

    sufficiency, effective_monthly = _income_sufficiency(
        coop_income_monthly=income["coop_income_monthly_nrs"],
        remittance_monthly=income["remittance_monthly_nrs"],
        hundi=income["hundi"],
        requested_amount=requested,
        coop_verified=income["coop_verified"],
        regularity_score=regularity
    )

    debt = _debt_signal(
        cib_clean=credit["cib_clean"],
        existing_loans_nrs=credit["existing_loans_nrs"],
        microfinance_member=credit["microfinance_member"],
    )

    geo_risk = _geographic_risk(
        zone=zone,
        land_type=land["land_type"],
        land_grade=land["land_grade"],
    )

    vector = FeatureVector(
        collateral_strength=collateral,
        income_regularity=regularity,
        income_sufficiency=sufficiency,
        debt_signal=debt,
        geographic_risk=geo_risk,
        hundi_applied=hundi_applied,
        gulf_gap_applied=gulf_gap_applied,
        fsv_confidence=fsv_result.confidence,
        effective_monthly_income=effective_monthly,
    )

    logger.debug(
        "Features engineered — %s: "
        "collateral=%.3f regularity=%.3f sufficiency=%.3f "
        "debt=%.3f geo=%.3f",
        profile.get("farmer_name", "unknown"),
        collateral, regularity, sufficiency, debt, geo_risk,
    )

    return vector
def engineer_features_batch(profiles: list[dict],fsv_calculator: Optional[FSVCalculator] = None,) -> list[FeatureVector]:
    if fsv_calculator is None:
        fsv_calculator = FSVCalculator()

    vectors = []
    for profile in profiles:
        vector = engineer_features(profile, fsv_calculator=fsv_calculator)
        vectors.append(vector)

    logger.info(f"Engineered features for {len(vectors)} profiles")
    return vectors

if __name__ == "__main__":
    import json
    from pathlib import Path

    logging.basicConfig(level=logging.INFO)

    profiles_path = Path(__file__).parents[3] / "data" / "synthetic_profiles.json"
    with open(profiles_path) as f:
        profiles = json.load(f)["profiles"]

    calc = FSVCalculator()

    # --- Ramesh detailed check ---
    ramesh = profiles[0]
    vector = engineer_features(ramesh, fsv_calculator=calc)

    print("\n--- Ramesh Feature Vector ---")
    print(f"Collateral Strength : {vector.collateral_strength:.4f}")
    print(f"Income Regularity   : {vector.income_regularity:.4f}")
    print(f"Income Sufficiency  : {vector.income_sufficiency:.4f}")
    print(f"Debt Signal         : {vector.debt_signal:.4f}")
    print(f"Geographic Risk     : {vector.geographic_risk:.4f}")
    print(f"\nHundi applied       : {vector.hundi_applied}")
    print(f"Gulf gap applied    : {vector.gulf_gap_applied}")
    print(f"FSV confidence      : {vector.fsv_confidence}")
    print(f"Effective income    : NRs {vector.effective_monthly_income:,.0f}/mo")

    weighted = sum(
        vector.to_dict()[dim] * FEATURE_WEIGHTS[dim]
        for dim in FEATURE_NAMES
    )
    print(f"\nWeighted score (rule-based): {weighted * 100:.2f}/100")
    print(f"Paper expected             : 71/100")

   
    expected_scores = [71, 54, 63, 38, 84, 49]
    names = ["Ramesh", "Sita", "Hari", "Maya", "Bir", "Ganga"]

    print("\n--- All 6 Profiles ---")
    for i, (name, expected) in enumerate(zip(names, expected_scores)):
        v = engineer_features(profiles[i], fsv_calculator=calc)
        computed = sum(
            v.to_dict()[dim] * FEATURE_WEIGHTS[dim]
            for dim in FEATURE_NAMES
        ) * 100
        diff = computed - expected
        status = "approved:" if abs(diff) <= 5 else "rejected:"
        print(f"{status} {name:10} expected={expected} computed={computed:.1f} diff={diff:+.1f}")