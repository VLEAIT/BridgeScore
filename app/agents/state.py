from typing import TypedDict, Optional, Any


class BridgeScoreState(TypedDict, total=False):

    application_id:         str
    farmer_name:            str
    district:               str
    zone:                   str        
    citizenship_number:     str
    phone_number:           str

    document_path:          Optional[str]
    lalpurja_verified:      bool
    malpot_cross_checked:   bool
    ocr_confidence:         float
    ocr_raw_text:           str
    lalpurja_fields:        dict     
    land_area_hectares:     float
    land_type:              str       
    land_grade:             str      
    sarkaari_mool_nrs:      float
    malpot_verified:        bool
    existing_mortgage:      bool
    fsv_nrs:                float     
    max_loan_from_fsv:      float     
    fsv_confidence:         float
    dva_soft_blocks:        list[str]  
    dva_hard_blocks:        list[str] 

    coop_income_monthly:    float
    coop_verified:          bool
    remittance_monthly:     float
    remittance_channel:     str      
    remittance_months_history: int
    remittance_gap_months:  int
    hundi:                  bool
    hundi_proxy_count:      int
    hundi_applied:          bool
    gulf_gap_applied:       bool
    effective_monthly_income: float
    total_income_capacity:  float      
    feature_vector:         dict       
    credit_score:           float      
    recommendation:         str     
    confidence_upper:       float
    top_shap_factors:       list[dict] 
    all_shap_values:        dict      

    cib_clean:              bool
    existing_loans_nrs:     float
    microfinance_member:    bool
    nrb_compliant:          bool
    compliance_checks:      list[dict] 
    fraud_flags:            list[str]
    recommended_max_amount: float      

    final_decision:         str        
    approved_amount_nrs:    float
    conditions:             list[str]  
    action_items:           list[str] 
    nepali_explanation:     str        
    processing_time_seconds: float
    created_at:str

    audit_trail:            list[str]


def initial_state(application: dict) -> BridgeScoreState:
   
    return BridgeScoreState(
        application_id=application.get("application_id", ""),
        farmer_name=application.get("farmer_name", ""),
        district=application.get("district", ""),
        zone=application.get("zone", "hill"),
        citizenship_number=application.get("citizenship_number", ""),
        phone_number=application.get("phone_number", ""),
        document_path=application.get("lalpurja_image_path"),
        created_at=application.get("created_at",""),

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

    
        credit_score=0.0,
        recommendation="",
        confidence_lower=0.0,
        confidence_upper=0.0,
        top_shap_factors=[],
        all_shap_values={},

    
        cib_clean=True,
        existing_loans_nrs=0.0,
        microfinance_member=False,
        nrb_compliant=True,
        compliance_checks=[],
        fraud_flags=[],
        recommended_max_amount=0.0,

     
        final_decision="",
        approved_amount_nrs=0.0,
        conditions=[],
        action_items=[],
        nepali_explanation="",
        processing_time_seconds=0.0,

   
        audit_trail=[],
    )