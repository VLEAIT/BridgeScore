

import logging
from app.agents.state import BridgeScoreState
from app.ml.scoring.features import engineer_features, FEATURE_NAMES
from app.ml.fsv import FSVCalculator, FSVResult
from app.integrations.remittance import fetch_remittance_history
from decimal import Decimal

logger = logging.getLogger("bridgescore.agents.iia")


def iia_node(state: BridgeScoreState) -> dict:

    logger.info("IIA: Starting income inference")
    audit = list(state.get("audit_trail", []))
    audit.append("IIA: Inferring income from cooperative and remittance channels...")

    remittance_channel = state.get("remittance_channel", "None")
    remittance_monthly = float(state.get("remittance_monthly", 0.0))
    hundi = remittance_channel == "Hundi"

    months_history = 0
    gap_months = 0
    hundi_proxy_count = 0

    if remittance_channel not in ("None", "Hundi"):
        try:
            remittance_data = fetch_remittance_history(
                citizenship_number=state.get("citizenship_number", ""),
                channel=remittance_channel,
            )
            months_history = remittance_data.get("months_history", 0)
            gap_months = remittance_data.get("gap_months", 0)
            audit.append(
                f"IIA: Remittance history — "
                f"{months_history} months, {gap_months} gap months"
            )
        except Exception as e:
            logger.warning(f"Remittance API failed: {e}")
            audit.append("IIA: Remittance API unreachable — using declared amount only")

    elif hundi:
        hundi_proxy_count = 2  
        audit.append("IIA: Hundi detected — applying 35% confidence discount")

    profile = {
        "farmer_name":  state.get("farmer_name", ""),
        "district":     state.get("district", ""),
        "zone":         state.get("zone", "hill"),
        "land": {
            "land_area_hectares": state.get("land_area_hectares", 0.0),
            "land_type":          state.get("land_type", "Khet"),
            "land_grade":         state.get("land_grade", "Aabal"),
            "sarkaari_mool_nrs":  state.get("sarkaari_mool_nrs", 0.0),
            "malpot_verified":    state.get("malpot_verified", False),
            "existing_mortgage":  state.get("existing_mortgage", False),
        },
        "income": {
            "coop_income_monthly_nrs":  float(state.get("coop_income_monthly", 0.0)),
            "coop_verified":            state.get("coop_verified", False),
            "remittance_monthly_nrs":   remittance_monthly,
            "remittance_channel":       remittance_channel,
            "remittance_months_history": months_history,
            "remittance_gap_months":    gap_months,
            "hundi":                    hundi,
            "hundi_proxy_signals":      ["esewa"] * hundi_proxy_count,
        },
        "credit": {
            "cib_clean":          state.get("cib_clean", True),
            "existing_loans_nrs": float(state.get("existing_loans_nrs", 0.0)),
            "microfinance_member": state.get("microfinance_member", False),
        },
        "application": {
            "requested_amount_nrs": float(state.get("requested_amount_nrs", 200000)),
            "consent_given":        True,
        },
    }

    fsv_calc = FSVCalculator()
    vector = engineer_features(profile, fsv_calculator=fsv_calc)

    effective_monthly = vector.effective_monthly_income
    total_capacity = effective_monthly * 12

    audit.append(
        f"IIA: Effective monthly income = NRs {effective_monthly:,.0f} "
        f"| 12x capacity = NRs {total_capacity:,.0f}"
    )
    audit.append(
        f"IIA: Features — "
        f"collateral={vector.collateral_strength:.3f} "
        f"regularity={vector.income_regularity:.3f} "
        f"sufficiency={vector.income_sufficiency:.3f}"
    )

    return {
        "remittance_months_history": months_history,
        "remittance_gap_months":     gap_months,
        "hundi":                     hundi,
        "hundi_proxy_count":         hundi_proxy_count,
        "hundi_applied":             vector.hundi_applied,
        "gulf_gap_applied":          vector.gulf_gap_applied,
        "effective_monthly_income":  effective_monthly,
        "total_income_capacity":     total_capacity,
        "feature_vector":            vector.to_dict(),
        "audit_trail":               audit,
    }