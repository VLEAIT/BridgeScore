from typing import TypedDict, Optional, Any


class BridgeScoreState(TypedDict, total=False):

    # ── Application identity ──────────────────────────────
    application_id:         str
    farmer_name:            str
    district:               str
    zone:                   str        # terai / hill / mountain
    citizenship_number:     str
    phone_number:           str

    # ── Document & Land (DVA writes) ─────────────────────
    document_path:          Optional[str]
    lalpurja_verified:      bool
    malpot_cross_checked:   bool
    ocr_confidence:         float
    ocr_raw_text:           str
    lalpurja_fields:        dict       # raw parsed fields from lalpurja_parser
    land_area_hectares:     float
    land_type:              str        # Khet / Bari / Gharbari
    land_grade:             str        # Aabal / Doyam / Sim / Chahar
    sarkaari_mool_nrs:      float
    malpot_verified:        bool
    existing_mortgage:      bool
    fsv_nrs:                float      # Forced Sale Value
    max_loan_from_fsv:      float      # fsv * 0.60
    fsv_confidence:         float
    dva_soft_blocks:        list[str]  # non-fatal flags
    dva_hard_blocks:        list[str]  # fatal — stop processing

    # ── Income (IIA writes) ───────────────────────────────
    coop_income_monthly:    float
    coop_verified:          bool
    remittance_monthly:     float
    remittance_channel:     str        # IME / Prabhu / Hundi / None
    remittance_months_history: int
    remittance_gap_months:  int
    hundi:                  bool
    hundi_proxy_count:      int
    hundi_applied:          bool
    gulf_gap_applied:       bool
    effective_monthly_income: float
    total_income_capacity:  float      # effective_monthly * 12

    # ── Feature vector (IIA writes, CSA reads) ────────────
    feature_vector:         dict       # 5 dimension scores 0-1

    # ── Scoring (CSA writes) ──────────────────────────────
    credit_score:           float      # 0-100
    recommendation:         str        # Approve / Conditional Approve / Decline
    confidence_lower:       float
    confidence_upper:       float
    top_shap_factors:       list[dict] # top 3 SHAP contributors
    all_shap_values:        dict       # full SHAP for audit

    # ── Compliance (CA writes) ────────────────────────────
    cib_clean:              bool
    existing_loans_nrs:     float
    microfinance_member:    bool
    nrb_compliant:          bool
    compliance_checks:      list[dict] # each NRB rule + pass/fail
    fraud_flags:            list[str]
    recommended_max_amount: float      # CA computed ceiling

    # ── Final decision (OA writes) ────────────────────────
    final_decision:         str        # Approve / Conditional Approve / Decline
    approved_amount_nrs:    float
    conditions:             list[str]  # for Conditional Approve
    action_items:           list[str]  # for Decline — reapplication steps
    nepali_explanation:     str        # SMS text
    processing_time_seconds: float

    # ── Audit trail (all agents append) ──────────────────
    audit_trail:            list[str]


def initial_state(application: dict) -> BridgeScoreState:
    """
    Build initial state from ApplicationCreate payload.
    Called by FastAPI endpoint before graph invocation.
    """
    return BridgeScoreState(
        application_id=application.get("application_id", ""),
        farmer_name=application.get("farmer_name", ""),
        district=application.get("district", ""),
        zone=application.get("zone", "hill"),
        citizenship_number=application.get("citizenship_number", ""),
        phone_number=application.get("phone_number", ""),
        document_path=application.get("lalpurja_image_path"),

        # land defaults — overwritten by DVA
        lalpurja_verified=False,
        malpot_cross_checked=False,
        ocr_confidence=0.0,
        ocr_raw_text="",
        lalpurja_fields={},
        land_area_hectares=application.get("land_area_hectares", 0.0),
        land_type=application.get("land_type", "Khet"),
        land_grade=application.get("land_grade", "Aabal"),
        sarkaari_mool_nrs=0.0,
        malpot_verified=False,
        existing_mortgage=False,
        fsv_nrs=0.0,
        max_loan_from_fsv=0.0,
        fsv_confidence=0.0,
        dva_soft_blocks=[],
        dva_hard_blocks=[],

        # income defaults — overwritten by IIA
        coop_income_monthly=application.get("coop_income_monthly", 0.0),
        coop_verified=False,
        remittance_monthly=application.get("remittance_monthly", 0.0),
        remittance_channel=application.get("remittance_channel", "None"),
        remittance_months_history=0,
        remittance_gap_months=0,
        hundi=application.get("remittance_channel") == "Hundi",
        hundi_proxy_count=0,
        hundi_applied=False,
        gulf_gap_applied=False,
        effective_monthly_income=0.0,
        total_income_capacity=0.0,
        feature_vector={},

        # scoring defaults
        credit_score=0.0,
        recommendation="",
        confidence_lower=0.0,
        confidence_upper=0.0,
        top_shap_factors=[],
        all_shap_values={},

        # compliance defaults
        cib_clean=True,
        existing_loans_nrs=0.0,
        microfinance_member=False,
        nrb_compliant=True,
        compliance_checks=[],
        fraud_flags=[],
        recommended_max_amount=0.0,

        # final output defaults
        final_decision="",
        approved_amount_nrs=0.0,
        conditions=[],
        action_items=[],
        nepali_explanation="",
        processing_time_seconds=0.0,

        # audit trail
        audit_trail=[],
    )