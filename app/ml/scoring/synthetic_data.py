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


def score_income_sufficiency(coop_income_monthly:float,remittance_monthly:float,hundi:bool,requested_amount:float)->float:
    effective_remittance=(
        remittance_monthly*(1- HUNDI_CONFIDENCE_DISCOUNT)
        if hundi else remittance_monthly
    )
    total_monthly=coop_income_monthly+effective_remittance
    twelve_x_capacity=total_monthly*NRB_MONTHLY_INCOME_MULTIPLIER

    if requested_amount <= 0:
        return 0.0

    ratio =twelve_x_capacity/requested_amount
    return min(round(ratio/2.0,4),1.0)

def score_debt_signal(cib_clean:bool,existing_laons_nrs:float,micorfinance_member:bool,)->float:
    if not cib_clean:
        return 0.0
    if existing_loans_nrs==0 and not micrrofinance_member:
        return 1.0  
    if microfinance_member and existing_loans_nrs==0:
        return 0.85
    loan_penalty = min(existing_loans_nrs /500000,0.40)
    return max(0.0,round(0.80-loan_penalty,4))

def score_geographic_risk(zone:str,land_type:str,)->float:
    base=ZONE_BASE_SCORES.get(zone,0.50)
    bonus=LAND_TYPE_BONUS.get(land_type,0.0)
    return max(0.0,min(1.0,round(base+bonus,4)))

def calculate_score(profile: dict, fsv: float, zone: str) -> dict:
  
    income = profile["income"]
    land = profile["land"]
    credit = profile["credit"]
    application = profile["application"]

    dimensions = {
        "collateral_strength": score_collateral_strength(
            fsv=fsv,
            requested_amount=application["requested_amount_nrs"],
            zone=zone,
        ),
        "income_regularity": score_income_regularity(
            remittance_monthly=income["remittance_monthly_nrs"],
            remittance_months_history=income["remittance_months_history"],
            remittance_gap_months=income["remittance_gap_months"],
            hundi=income["hundi"],
            coop_income_monthly=income["coop_income_monthly_nrs"],
        ),
        "income_sufficiency": score_income_sufficiency(
            coop_income_monthly=income["coop_income_monthly_nrs"],
            remittance_monthly=income["remittance_monthly_nrs"],
            hundi=income["hundi"],
            requested_amount=application["requested_amount_nrs"],
        ),
        "debt_signal": score_debt_signal(
            cib_clean=credit["cib_clean"],
            existing_loans_nrs=credit["existing_loans_nrs"],
            microfinance_member=credit["microfinance_member"],
        ),
        "geographic_risk": score_geographic_risk(
            zone=zone,
            land_type=land["land_type"],
        ),
    }
    raw_score = sum(
        dimensions[dim] * WEIGHTS[dim]
        for dim in dimensions
    )
    final_score = round(raw_score * 100, 2)

    if final_score >= 65:
        decision = "Approve"
    elif final_score >= 45:
        decision = "Conditional Approve"
    else:
        decision = "Decline"

    return {
        "score": final_score,
        "decision": decision,
        "dimensions": dimensions,
    }

def vary_profile(anchor:dict,fsv_calculator:FSVCalculator,seed:int)->dict:
    random.seed(seed)
    zone=anchor["zone"]
    district = random.choice(DISTRICTS_BY_ZONE.get(zone, DISTRICTS_BY_ZONE["hill"]))
    land_type = random.choice(["Khet", "Bari", "Gharbari"])
    land_grade = random.choice(["Aabal", "Doyam", "Sim", "Chahar"])
    land_area = round(random.uniform(0.1, 2.0), 2)
    coop_income = random.randint(2000, 50000)
    remittance = random.randint(0, 80000)
    hundi = random.random() < 0.35 
    channel = "Hundi" if hundi else random.choice(["IME", "Prabhu", "None"])
    months_history = 0 if hundi else random.randint(0, 24)
    gap_months = random.randint(0, 6) if months_history > 0 else 0
    cib_clean = random.random() < 0.85  
    existing_loans = random.randint(0, 300000) if random.random() < 0.3 else 0
    microfinance = random.random() < 0.25
    monthly_total = coop_income + remittance
    requested = random.randint(
        max(50000, int(monthly_total * 3)),
        min(1000000, int(monthly_total * 20))
    )

    malpot_verified = random.random() < 0.70 
    tier_mool = {
        "urban": 1500000, "semi_urban": 600000,
        "rural": 250000, "remote": 70000
    }
    fsv_result = fsv_calculator.calculate(
        district=district,
        land_grade=land_grade,
        land_area_hectares=land_area,
        sarkaari_mool=Decimal(str(
            int(tier_mool.get("rural", 250000) * land_area)
        )),
        malpot_verified=malpot_verified,
    )

    profile = {
        "id": f"synthetic_{seed}",
        "farmer_name": f"Synthetic_{seed}",
        "district": district,
        "zone": zone,
        "land": {
            "land_area_hectares": land_area,
            "land_type": land_type,
            "land_grade": land_grade,
            "sarkaari_mool_nrs": int(fsv_result.sarkaari_mool),
            "malpot_verified": malpot_verified,
            "existing_mortgage": False,
        },
        "income": {
            "coop_income_monthly_nrs": coop_income,
            "coop_verified": random.random() < 0.80,
            "remittance_monthly_nrs": remittance,
            "remittance_channel": channel,
            "remittance_months_history": months_history,
            "remittance_gap_months": gap_months,
            "hundi": hundi,
            "hundi_proxy_signals": ["esewa_transactions"] if hundi else [],
        },
        "credit": {
            "cib_clean": cib_clean,
            "existing_loans_nrs": existing_loans,
            "microfinance_member": microfinance,
        },
        "application": {
            "requested_amount_nrs": requested,
            "consent_given": True,
        },
    }

    scoring = calculate_score(profile, float(fsv_result.fsv), zone)
    profile["expected"] = {
        "fsv_nrs": float(fsv_result.fsv),
        "max_loan_nrs": float(fsv_result.max_loan_amount),
        "score": scoring["score"],
        "decision": scoring["decision"],
        "dimensions": scoring["dimensions"],
    }

    return profile

def generate(n_variations: int = 494) -> list[dict]:

    fsv_calculator = FSVCalculator()

    with open(ANCHOR_PROFILES_PATH, "r", encoding="utf-8") as f:
        anchors = json.load(f)["profiles"]

    logger.info(f"Loaded {len(anchors)} anchor profiles")

    scored_anchors = []
    for anchor in anchors:
        fsv_result = fsv_calculator.calculate(
            district=anchor["district"],
            land_grade=anchor["land"]["land_grade"],
            land_area_hectares=anchor["land"]["land_area_hectares"],
            sarkaari_mool=Decimal(str(anchor["land"]["sarkaari_mool_nrs"])),
            malpot_verified=anchor["land"]["malpot_verified"],
        )
        scoring = calculate_score(
            anchor, float(fsv_result.fsv), anchor["zone"]
        )
        anchor["computed"] = {
            "fsv_nrs": float(fsv_result.fsv),
            "score": scoring["score"],
            "decision": scoring["decision"],
            "dimensions": scoring["dimensions"],
        }
        scored_anchors.append(anchor)
        logger.info(
            f"{anchor['farmer_name']:10} → "
            f"expected={anchor['expected']['score']} "
            f"computed={scoring['score']} "
            f"decision={scoring['decision']}"
        )

    variations = []
    for i in range(n_variations):
        anchor = anchors[i % len(anchors)]  
        variation = vary_profile(anchor, fsv_calculator, seed=i + 100)
        variations.append(variation)

    all_profiles = scored_anchors + variations
    logger.info(
        f"Generated {len(all_profiles)} profiles "
        f"({len(scored_anchors)} anchors + {len(variations)} variations)"
    )
    return all_profiles

def save(profiles: list[dict]) -> None:
    output = {
        "_metadata": {
            "total_profiles": len(profiles),
            "anchor_profiles": 6,
            "synthetic_variations": len(profiles) - 6,
            "description": "BridgeScore XGBoost training dataset",
        },
        "profiles": profiles,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(profiles)} profiles to {OUTPUT_PATH}")

    
    

                         


