# app/agents/orchestrator.py

import logging
import time
from app.agents.state import BridgeScoreState

logger = logging.getLogger("bridgescore.agents.oa")

NEPALI_TEMPLATES = {
    "Approve": (
        "तपाईंको आवेदन स्वीकृत भयो। "
        "स्वीकृत ऋण रकम: NRs {amount}। "
        "कृपया नजिकको शाखामा सम्पर्क गर्नुहोस्।"
    ),
    "Conditional Approve": (
        "तपाईंको आवेदन सर्तसहित स्वीकृत भयो। "
        "स्वीकृत ऋण रकम: NRs {amount}। "
        "थप कागजात: {conditions}"
    ),
    "Decline": (
        "तपाईंको आवेदन अस्वीकृत भयो। "
        "कारण: {reasons}। "
        "३ महिना पछि पुनः आवेदन दिनुहोस्।"
    ),
}


def oa_node(state: BridgeScoreState) -> dict:
    """
    Orchestrator Agent — final decision synthesis.

    Reads:  credit_score, recommendation, nrb_compliant,
            max_loan_from_fsv, recommended_max_amount,
            dva_hard_blocks, compliance_checks
    Writes: final_decision, approved_amount_nrs, conditions,
            action_items, nepali_explanation, processing_time_seconds
    """
    logger.info("OA: Synthesizing final decision")
    audit = list(state.get("audit_trail", []))
    audit.append("OA: Synthesizing final credit decision...")

    score = float(state.get("credit_score", 0.0))
    recommendation = state.get("recommendation", "Decline")
    nrb_compliant = state.get("nrb_compliant", True)
    hard_blocks = state.get("dva_hard_blocks", [])
    max_from_fsv = float(state.get("max_loan_from_fsv", 0.0))
    recommended_max = float(state.get("recommended_max_amount", 0.0))
    conditions = []
    action_items = []

    # --- hard block override ---
    if hard_blocks:
        final_decision = "Decline"
        approved_amount = 0.0
        action_items = [
            f"Resolve document issue: {block}"
            for block in hard_blocks
        ]
        audit.append(f"OA: Hard blocks triggered Decline: {hard_blocks}")

    # --- NRB non-compliant override ---
    elif not nrb_compliant:
        final_decision = "Decline"
        approved_amount = 0.0
        action_items = [
            "Resolve CIB default before reapplying",
            "Reapply after 3 months with clean credit record",
        ]
        audit.append("OA: NRB non-compliance triggered Decline")

    # --- normal scoring path ---
    elif recommendation == "Approve":
        final_decision = "Approve"
        approved_amount = min(max_from_fsv, recommended_max)

    elif recommendation == "Conditional Approve":
        final_decision = "Conditional Approve"
        approved_amount = min(max_from_fsv * 0.90, recommended_max)

        # generate conditions based on soft blocks
        soft_blocks = state.get("dva_soft_blocks", [])
        if not state.get("lalpurja_verified"):
            conditions.append("Submit cooperative membership certificate")
        if soft_blocks:
            conditions.append("Provide verified Lalpurja document")
        if not conditions:
            conditions.append("Submit additional income verification")

    else:
        final_decision = "Decline"
        approved_amount = 0.0
        top_factors = state.get("top_shap_factors", [])
        if top_factors:
            action_items = [
                f"Improve {f['display_label']} before reapplying"
                for f in top_factors[:2]
            ]
        action_items.append("Reapply after 3 months")

    # --- Nepali explanation ---
    template = NEPALI_TEMPLATES.get(final_decision, NEPALI_TEMPLATES["Decline"])
    nepali_explanation = template.format(
        amount=f"{approved_amount:,.0f}",
        conditions="、".join(conditions) if conditions else "",
        reasons="、".join(action_items[:2]) if action_items else "स्कोर अपर्याप्त",
    )

    processing_time = float(state.get("_start_time", time.time()))
    processing_seconds = round(time.time() - processing_time, 2)

    audit.append(
        f"OA: Final = {final_decision} | "
        f"Amount = NRs {approved_amount:,.0f} | "
        f"Time = {processing_seconds}s"
    )

    return {
        "final_decision":          final_decision,
        "approved_amount_nrs":     approved_amount,
        "conditions":              conditions,
        "action_items":            action_items,
        "nepali_explanation":      nepali_explanation,
        "processing_time_seconds": processing_seconds,
        "audit_trail":             audit,
    }