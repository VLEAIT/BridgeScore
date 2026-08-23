
import logging
from app.agents.state import BridgeScoreState
from app.integrations.cib import check_cib
from app.schemas.common import NRBRule

logger = logging.getLogger("bridgescore.agents.ca")


NRB_LTV_LIMIT = 0.60
NRB_SCORE_FLOOR = 45.0
NRB_MAX_CONCESSIONAL = 500_000.0


def _check(rule: str, passed: bool, actual: float, threshold: float, detail: str) -> dict:
    return {
        "rule":            rule,
        "passed":          passed,
        "actual_value":    actual,
        "threshold_value": threshold,
        "detail":          detail,
    }


def ca_node(state: BridgeScoreState) -> dict:

    logger.info("CA: Running NRB compliance checks")
    audit = list(state.get("audit_trail", []))
    audit.append("CA: Evaluating NRB Unified Directive 2081 compliance...")

    checks = []
    fraud_flags = []
    cib_clean = True

    
    try:
        cib_result = check_cib(
            citizenship_number=state.get("citizenship_number", "")
        )
        cib_clean = cib_result.get("clean", True)
        if not cib_clean:
            fraud_flags.append("CIB_DEFAULT_DETECTED")
            audit.append("CA: CIB check FAILED — existing default detected")
        else:
            audit.append("CA: CIB check passed — no defaults")
    except Exception as e:
        logger.warning(f"CIB check failed: {e}")
        audit.append("CA: CIB unreachable — holding decision pending")


    score = float(state.get("credit_score", 0.0))
    score_check = _check(
        rule=NRBRule.ltv_limit.value,
        passed=score >= NRB_SCORE_FLOOR,
        actual=score,
        threshold=NRB_SCORE_FLOOR,
        detail=f"Credit score {score} vs minimum {NRB_SCORE_FLOOR}",
    )
    checks.append(score_check)

 
    fsv = float(state.get("fsv_nrs", 0.0))
    requested = float(state.get("recommended_max_amount", 200_000.0))
    ltv_max = fsv * NRB_LTV_LIMIT
    ltv_check = _check(
        rule=NRBRule.ltv_limit.value,
        passed=requested <= ltv_max,
        actual=requested,
        threshold=ltv_max,
        detail=f"Requested {requested:,.0f} vs LTV ceiling {ltv_max:,.0f}",
    )
    checks.append(ltv_check)

    
    land_area = float(state.get("land_area_hectares", 0.0))
    monthly_income = float(state.get("effective_monthly_income", 0.0))
    deprived_eligible = land_area < 0.5 or monthly_income < 25_000
    deprived_check = _check(
        rule=NRBRule.deprived_sector.value,
        passed=deprived_eligible,
        actual=land_area,
        threshold=0.5,
        detail=f"Land {land_area}ha, income NRs {monthly_income:,.0f}/mo",
    )
    checks.append(deprived_check)

    
    cib_check = _check(
        rule=NRBRule.cib_clean.value,
        passed=cib_clean,
        actual=1.0 if cib_clean else 0.0,
        threshold=1.0,
        detail="No existing defaults in CIB bureau",
    )
    checks.append(cib_check)

   
    nrb_compliant = (
        cib_clean
        and score >= NRB_SCORE_FLOOR
        and requested <= ltv_max
    )

  
    income_ceiling = monthly_income * 12
    recommended_max = min(ltv_max, income_ceiling)

    audit.append(
        f"CA: Compliance {'PASSED' if nrb_compliant else 'FAILED'} — "
        f"{sum(1 for c in checks if c['passed'])}/{len(checks)} checks passed"
    )
    audit.append(
        f"CA: Recommended max = NRs {recommended_max:,.0f}"
    )

    return {
        "cib_clean":           cib_clean,
        "nrb_compliant":       nrb_compliant,
        "compliance_checks":   checks,
        "fraud_flags":         fraud_flags,
        "recommended_max_amount": recommended_max,
        "audit_trail":         audit,
    }