

import time
import json
import sys
import os
from urllib.error import URLError
from urllib.request import urlopen
from pathlib import Path
import hashlib

import streamlit as st
import pandas as pd
import numpy as np


st.set_page_config(
    page_title="BridgeScore",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)


APPROVE_COLOR   = "#2D6A4F"  
CONDITIONAL_COLOR = "#E9A825"
DECLINE_COLOR   = "#C0392B" 
ACCENT          = "#2D6A4F"
SLATE           = "#1C2B3A"
CREAM           = "#F8F5EE"


st.markdown("""
<style>
  /* Base */
  [data-testid="stAppViewContainer"] {
    background: #F8F5EE;
    font-family: 'Inter', sans-serif;
  }
  [data-testid="stHeader"] { background: transparent; }

  /* Header strip */
  .bs-header {
    background: #1C2B3A;
    padding: 1.2rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  .bs-header h1 {
    color: #F8F5EE;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.5px;
  }
  .bs-header p {
    color: #94A3B8;
    font-size: 0.85rem;
    margin: 0;
  }
  .bs-badge {
    background: #2D6A4F;
    color: white;
    font-size: 0.7rem;
    padding: 3px 10px;
    border-radius: 20px;
    font-weight: 600;
    letter-spacing: 0.5px;
  }

  /* Cards */
  .bs-card {
    background: white;
    border-radius: 12px;
    padding: 1.4rem;
    border: 1px solid #E8E3D9;
    margin-bottom: 1rem;
  }
  .bs-card-title {
    font-size: 0.75rem;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  /* Decision banner */
  .decision-approve {
    background: linear-gradient(135deg, #2D6A4F 0%, #40916C 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 1rem;
  }
  .decision-conditional {
    background: linear-gradient(135deg, #B7791F 0%, #E9A825 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 1rem;
  }
  .decision-decline {
    background: linear-gradient(135deg, #922B21 0%, #C0392B 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 1rem;
  }
  .decision-label {
    font-size: 0.75rem;
    opacity: 0.85;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
  }
  .decision-value {
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0.3rem 0;
  }
  .decision-amount {
    font-size: 1rem;
    opacity: 0.9;
  }

  /* Score gauge */
  .score-ring-container {
    text-align: center;
    padding: 1rem 0;
  }
  .score-ring {
    --score: 0;
    --ring-color: #2D6A4F;
    width: 156px;
    height: 156px;
    margin: 0 auto 0.8rem;
    border-radius: 50%;
    display: grid;
    place-items: center;
    background: conic-gradient(var(--ring-color) calc(var(--score) * 1%), #E8E3D9 0);
    animation: ring-grow 1s ease-out;
  }
  .score-ring-inner {
    width: 132px;
    height: 132px;
    border-radius: 50%;
    background: white;
    display: grid;
    place-items: center;
  }
  @keyframes ring-grow { from { opacity: 0.25; transform: scale(0.88); } to { opacity: 1; transform: scale(1); } }
  .score-number {
    font-size: 3rem;
    font-weight: 800;
    color: #1C2B3A;
    line-height: 1;
  }
  .score-label {
    font-size: 0.75rem;
    color: #64748B;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  .score-bar-container {
    background: #E8E3D9;
    border-radius: 8px;
    height: 10px;
    margin: 0.8rem 0;
    overflow: hidden;
  }
  .score-bar {
    height: 10px;
    border-radius: 8px;
    transition: width 0.8s ease;
  }

  /* SHAP factors */
  .shap-factor {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.6rem 0;
    border-bottom: 1px solid #F1EDE4;
  }
  .shap-factor:last-child { border-bottom: none; }
  .shap-label { font-size: 0.85rem; color: #374151; font-weight: 500; }
  .shap-bar-wrap {
    flex: 1;
    margin: 0 1rem;
    background: #F1EDE4;
    border-radius: 4px;
    height: 6px;
    overflow: hidden;
  }
  .shap-bar-pos {
    height: 6px;
    border-radius: 4px;
    background: #2D6A4F;
  }
  .shap-val { font-size: 0.8rem; color: #64748B; font-weight: 600; width: 50px; text-align: right; }

  /* OCR panel */
  .ocr-panel {
    background: #1C2B3A;
    border-radius: 10px;
    padding: 1rem;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem;
    color: #94A3B8;
    max-height: 300px;
    overflow-y: auto;
    line-height: 1.6;
  }
  .ocr-highlight { color: #E9A825; }

  /* Agent timeline */
  .agent-step {
    display: flex;
    gap: 0.8rem;
    padding: 0.5rem 0;
    align-items: flex-start;
  }
  .agent-dot {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: #2D6A4F;
    color: white;
    font-size: 0.7rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 2px;
  }
  .agent-dot-pending {
    background: #E8E3D9;
    color: #94A3B8;
  }
  .agent-content { flex: 1; }
  .agent-name { font-size: 0.82rem; font-weight: 600; color: #1C2B3A; }
  .agent-desc { font-size: 0.78rem; color: #64748B; margin-top: 1px; }

  /* Nepali SMS box */
  .nepali-sms {
    background: #1C2B3A;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    color: #F8F5EE;
    font-size: 0.9rem;
    line-height: 1.7;
    border-left: 4px solid #E9A825;
  }

  /* Stat pill */
  .stat-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: white;
    border: 1px solid #E8E3D9;
    border-radius: 20px;
    padding: 0.3rem 0.8rem;
    font-size: 0.8rem;
    color: #374151;
    margin: 0.2rem;
  }
  .stat-pill strong { color: #1C2B3A; }

  /* Tabs */
  [data-testid="stTabs"] button {
    font-weight: 600;
    font-size: 0.9rem;
  }

  /* Hide streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }

  /* NRB compliance checks */
  .check-pass { color: #2D6A4F; font-weight: 600; }
  .check-fail { color: #C0392B; font-weight: 600; }

  /* Field extracted */
  .field-row {
    display: flex;
    justify-content: space-between;
    padding: 0.4rem 0;
    border-bottom: 1px dashed #F1EDE4;
    font-size: 0.85rem;
  }
  .field-row:last-child { border-bottom: none; }
  .field-key { color: #64748B; }
  .field-val { color: #1C2B3A; font-weight: 500; }

  @media (max-width: 760px) {
    .bs-header { padding: 1rem; margin-bottom: 1rem; }
    .bs-header h1 { font-size: 1.45rem; }
    .bs-header p { font-size: 0.75rem; }
    .bs-card { padding: 1rem; }
    .score-ring { width: 132px; height: 132px; }
    .score-ring-inner { width: 112px; height: 112px; }
  }

  /* Dark product interface — presentation only */
  [data-testid="stAppViewContainer"] {
    background:
      radial-gradient(circle at 8% -10%, rgba(56, 189, 248, 0.12), transparent 30rem),
      radial-gradient(circle at 95% 2%, rgba(74, 222, 128, 0.10), transparent 27rem),
      #09111F;
    color: #E5EDF8;
  }
  [data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    opacity: 0.32;
    background-image: linear-gradient(rgba(148,163,184,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.035) 1px, transparent 1px);
    background-size: 28px 28px;
  }
  .block-container { max-width: 1380px; padding-top: 1.35rem; padding-bottom: 2rem; }
  .bs-header {
    background: linear-gradient(115deg, #0E1C31 0%, #132942 58%, #12352E 100%);
    border: 1px solid rgba(148, 163, 184, 0.18);
    box-shadow: 0 18px 44px rgba(0, 0, 0, 0.24);
    position: relative;
    overflow: hidden;
  }
  .bs-header::after { content: ""; position: absolute; width: 180px; height: 180px; right: -50px; top: -80px; border: 1px solid rgba(110,231,183,.18); border-radius: 50%; box-shadow: 0 0 0 28px rgba(110,231,183,.035), 0 0 0 56px rgba(110,231,183,.02); }
  .bs-header h1 { color: #F8FAFC; letter-spacing: -0.8px; }
  .bs-header p { color: #AABCD1; }
  .bs-badge { background: rgba(52, 211, 153, .14); color: #86EFAC; border: 1px solid rgba(110,231,183,.3); }
  .bs-card {
    background: linear-gradient(145deg, rgba(20, 34, 55, .94), rgba(13, 24, 42, .94));
    border: 1px solid rgba(148, 163, 184, 0.16);
    box-shadow: 0 10px 25px rgba(0,0,0,.16);
  }
  .bs-card-title, .score-label, .field-key, .agent-desc, .shap-val { color: #93A9C4; }
  .field-val, .agent-name, .shap-label, .stat-pill strong { color: #E5EDF8; }
  .field-row, .shap-factor { border-color: rgba(148,163,184,.14); }
  .score-ring-inner { background: #111E31; box-shadow: inset 0 0 0 1px rgba(148,163,184,.14); }
  .score-bar-container, .shap-bar-wrap { background: #24354D; }
  .ocr-panel { background: #08111E; border: 1px solid rgba(148,163,184,.12); color: #BED0E5; }
  .nepali-sms { background: linear-gradient(135deg, #13283B, #102236); box-shadow: inset 0 0 0 1px rgba(148,163,184,.12); }
  .stat-pill { background: #14253B; border-color: rgba(148,163,184,.18); color: #C6D5E7; }
  .agent-dot-pending { background: #27384F; color: #9FB2C8; }
  .agent-dot { box-shadow: 0 0 0 4px rgba(45,106,79,.16); }
  [data-testid="stTabs"] [role="tablist"] { gap: .35rem; border-bottom: 1px solid rgba(148,163,184,.16); }
  [data-testid="stTabs"] button { color: #9FB2C8; border-radius: 8px 8px 0 0; }
  [data-testid="stTabs"] button[aria-selected="true"] { color: #A7F3D0; background: rgba(52,211,153,.1); }
  [data-testid="stTabs"] [data-baseweb="tab-highlight"] { background: #34D399; }
  [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-baseweb="select"] > div {
    background: #0C1829 !important; color: #E5EDF8 !important; border-color: #2B405B !important; border-radius: 8px !important;
  }
  [data-testid="stTextInput"] input:focus, [data-testid="stNumberInput"] input:focus { border-color: #34D399 !important; box-shadow: 0 0 0 1px #34D399 !important; }
  [data-testid="stSelectbox"] label, [data-testid="stTextInput"] label, [data-testid="stNumberInput"] label, [data-testid="stCheckbox"] label, [data-testid="stToggle"] label { color: #C6D5E7 !important; }
  [data-testid="stFileUploader"] { background: rgba(15, 29, 48, .72); border-radius: 10px; border: 1px dashed #355170; padding: .35rem; }
  [data-testid="stFileUploader"] small, [data-testid="stCaptionContainer"] { color: #8FA5C0 !important; }
  .stButton > button { background: linear-gradient(135deg, #1C8B68, #27A878); border: 1px solid #5EE2A5; color: #F4FFFB; border-radius: 8px; font-weight: 700; box-shadow: 0 7px 18px rgba(16,185,129,.18); }
  .stButton > button:hover { background: linear-gradient(135deg, #22A87B, #36C993); border-color: #A7F3D0; }
  [data-testid="stDataFrame"], [data-testid="stMetric"] { border-radius: 10px; overflow: hidden; }
  [data-testid="stMetric"] { background: rgba(17, 31, 50, .7); border: 1px solid rgba(148,163,184,.13); padding: .7rem; }
  [data-testid="stMetricLabel"], [data-testid="stMetricValue"] { color: #E5EDF8 !important; }
  [data-testid="stAlert"] { background: rgba(25, 46, 67, .78); color: #D5E5F4; border: 1px solid rgba(125,211,252,.2); }
  [data-testid="stExpander"] { background: rgba(16, 29, 48, .78); border-color: rgba(148,163,184,.16); }
  [data-testid="stExpander"] summary { color: #C6D5E7; }
</style>
""", unsafe_allow_html=True)



st.markdown("""
<div class="bs-header">
  <div>
    <h1>🌾 BridgeScore</h1>
    <p>Autonomous Agricultural Credit Orchestration · Nepal Rastra Bank Compliant</p>
  </div>
  <span class="bs-badge">PROOF OF CONCEPT</span>
</div>
""", unsafe_allow_html=True)


def run_pipeline(application: dict) -> dict:
   
    try:
        project_root = Path(__file__).resolve().parents[2]
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        from app.agents.state import initial_state
        from app.agents.graph import pipeline

        state = initial_state(application)
        result = pipeline.invoke(state)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


API_BASE_URL = os.getenv("BRIDGESCORE_API_URL", "http://localhost:8000/api/v1")


@st.cache_data(ttl=15, show_spinner=False)
def fetch_application_history() -> tuple[list[dict], str | None]:
   
    try:
        with urlopen(f"{API_BASE_URL}/applications?skip=0&limit=100", timeout=4) as response:
            envelope = json.loads(response.read().decode("utf-8"))
        if not envelope.get("success"):
            return [], envelope.get("error") or "The API did not return a successful response."
        data = envelope.get("data", [])
        return (data if isinstance(data, list) else data.get("items", [])), None
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return [], f"Could not reach the API at {API_BASE_URL}: {exc}"


def run_mock_pipeline(application: dict) -> dict:

    time.sleep(2.5) 
    score = 78.3
    district = application.get("district", "Kavrepalanchok")
    coop = float(application.get("coop_income_monthly", 18000))
    remittance = float(application.get("hundi_proxy_base_monthly", application.get("remittance_monthly", 40000)))
    land_area = float(application.get("land_area_hectares", 0.5))
    land_grade = application.get("land_grade", "Aabal")
    channel = application.get("remittance_channel", "IME")

    if coop + remittance > 60000:
        score = 82.0
    elif coop + remittance > 40000:
        score = 71.0
    elif coop + remittance > 20000:
        score = 54.0
    else:
        score = 38.0

    if channel == "Hundi":
        score -= 12
    if land_grade == "Chahar":
        score -= 8
    if land_area < 0.3:
        score -= 5

    score = max(25.0, min(95.0, score))

    if score >= 65:
        decision = "Approve"
        amount = min(land_area * 320000 * 0.6, (coop + remittance) * 12 * 0.5)
    elif score >= 45:
        decision = "Conditional Approve"
        amount = min(land_area * 320000 * 0.5, (coop + remittance) * 10 * 0.5)
    else:
        decision = "Decline"
        amount = 0.0

    return {
        "success": True,
        "result": {
            "credit_score": round(score, 1),
            "final_decision": decision,
            "approved_amount_nrs": round(amount / 1000) * 1000,
            "recommendation": decision,
            "confidence_lower": round(score - 5, 1),
            "confidence_upper": round(score + 5, 1),
            "top_shap_factors": [
                {"feature": "income_regularity",   "display_label": "Income Regularity",         "contribution": 10.5},
                {"feature": "collateral_strength",  "display_label": "Land Collateral Strength",  "contribution": 9.2},
                {"feature": "income_sufficiency",   "display_label": "Income Sufficiency",        "contribution": 7.8},
            ],
            "all_shap_values": {
                "collateral_strength": 9.2,
                "income_regularity":   10.5,
                "income_sufficiency":  7.8,
                "debt_signal":         4.1,
                "geographic_risk":     2.3,
            },
            "lalpurja_verified": True,
            "malpot_cross_checked": True,
            "ocr_confidence": 0.87,
            "fsv_nrs": land_area * 516129 * 0.62,
            "max_loan_from_fsv": land_area * 516129 * 0.62 * 0.6,
            "fsv_confidence": 0.85,
            "effective_monthly_income": coop + (remittance * (0.65 if channel == "Hundi" else 1.0)),
            "nrb_compliant": score >= 45,
            "compliance_checks": [
                {"rule": "LTV_LIMIT",       "passed": True,        "actual_value": amount,  "threshold_value": land_area * 320000 * 0.6, "detail": "Loan within FSV ceiling"},
                {"rule": "DEPRIVED_SECTOR", "passed": land_area < 0.5, "actual_value": land_area, "threshold_value": 0.5, "detail": f"Land {land_area}ha"},
                {"rule": "CIB_CLEAN",       "passed": True,        "actual_value": 1.0,     "threshold_value": 1.0,  "detail": "No CIB defaults"},
            ],
            "conditions": ["Submit cooperative membership certificate"] if decision == "Conditional Approve" else [],
            "action_items": ["Establish formal remittance history", "Reapply in 3 months"] if decision == "Decline" else [],
            "nepali_explanation": (
                f"तपाईंको आवेदन {'स्वीकृत' if decision != 'Decline' else 'अस्वीकृत'} भयो। "
                + (f"स्वीकृत ऋण: NRs {amount:,.0f}।" if decision != "Decline" else "३ महिना पछि पुनः आवेदन दिनुहोस्।")
            ),
            "dva_soft_blocks": [],
            "dva_hard_blocks": [],
            "processing_time_seconds": 2.5,
            "audit_trail": [
                "DVA: Initiating Lalpurja verification...",
                f"DVA: OCR extracted fields (confidence=0.87)",
                f"DVA: Malpot cross-reference verified",
                f"DVA: FSV = NRs {land_area * 320000:,.0f} MaxLoan = NRs {land_area * 192000:,.0f}",
                "IIA: Inferring income from cooperative and remittance channels...",
                f"IIA: Effective monthly income = NRs {coop + remittance:,.0f}",
                f"CSA: Running XGBoost credit scoring model...",
                f"CSA: Score = {round(score, 1)}/100 → {decision}",
                "CA: Evaluating NRB Unified Directive 2081 compliance...",
                f"CA: Compliance {'PASSED' if score >= 45 else 'FAILED'}",
                f"OA: Final = {decision} | Amount = NRs {amount:,.0f} | Time = 2.5s",
            ],
        }
    }


tab1, tab2, tab3 = st.tabs(["🔍 Live Pipeline", "📊 Profile Explorer", "🗂️ Application History"])



with tab1:

    col_form, col_results = st.columns([1, 1.4], gap="large")

    with col_form:
        st.markdown('<div class="bs-card-title">📋 LOAN APPLICATION</div>', unsafe_allow_html=True)

        # Lalpurja upload
        st.markdown('<div class="bs-card">', unsafe_allow_html=True)
        st.markdown('<div class="bs-card-title">📄 LALPURJA DOCUMENT</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload Lalpurja photo",
            type=["png", "jpg", "jpeg"],
            help="Photo of the land ownership certificate (Lalpurja)",
            label_visibility="collapsed",
            key="lalpurja_upload",
        )
        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            file_hash = hashlib.sha256(file_bytes).hexdigest()
            needs_ocr = st.session_state.get("ocr_file_hash") != file_hash

            if needs_ocr:
                with st.spinner("Extracting fields via EasyOCR..."):
                    try:
                        import tempfile, os
                        from app.ml.ocr.paddle_ocr import LalpurjaOCR
                        from app.ml.ocr.lalpurja_parser import LalpurjaParser

                        with tempfile.NamedTemporaryFile(
                            delete=False,
                            suffix=Path(uploaded_file.name).suffix
                        ) as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name

                        ocr = LalpurjaOCR()
                        ocr_result = ocr.extract(tmp_path)
                        os.unlink(tmp_path)

                        if ocr_result.error:
                            st.error(f"OCR failed: {ocr_result.error}")
                            extracted = {}
                        else:
                            parser = LalpurjaParser()
                            parsed = parser.parse(ocr_result.raw_text)
                            extracted = {
                                "owner_name": parsed.owner_name,
                                "citizenship_number": parsed.citizenship_no,
                                "district": parsed.district,
                                "kitta_number": parsed.kitta_number,
                                "land_area_hectares": (
                                    parsed.area_sq_meters / 10_000
                                    if parsed.area_sq_meters is not None
                                    else None
                                ),
                                "land_type": None,
                                "land_grade": None,
                                "ward": None,
                                "has_existing_mortgage": False,
                                "is_valid_lalpurja": parsed.is_valid_lalpurja,
                                "extracted_fields": parsed.extracted_fields,
                            }

                            preview_col, fields_col = st.columns([1, 1.15])
                            with preview_col:
                                st.image(uploaded_file, caption="Uploaded Lalpurja", use_container_width=True)
                            with fields_col:
                                st.markdown('<div class="bs-card-title">📋 OCR EXTRACTED FIELDS</div>', unsafe_allow_html=True)
                                if extracted:
                                    ocr_preview = pd.DataFrame(
                                        [{"Field": key.replace("_", " ").title(), "Value": str(value)}
                                         for key, value in extracted.items() if value not in (None, "", False)]
                                    )
                                    st.dataframe(ocr_preview, hide_index=True, use_container_width=True)
                                else:
                                    st.caption("No structured fields were detected. You can enter them manually below.")

                            conf = ocr_result.confidence
                            conf_color = "#2D6A4F" if conf >= 0.7 else "#E9A825" if conf >= 0.5 else "#C0392B"
                            st.markdown(f"""
                            <div style="display:flex; align-items:center; gap:0.5rem;
                                        margin:0.5rem 0; font-size:0.8rem;">
                              <span style="color:{conf_color}; font-weight:700;">
                                {'✅' if conf >= 0.7 else '⚠️'} OCR Confidence: {conf:.0%}
                              </span>
                              <span style="color:#94A3B8;">·</span>
                              <span style="color:#94A3B8;">{len(ocr_result.lines)} lines extracted</span>
                            </div>
                            """, unsafe_allow_html=True)

                            # ── extracted fields table ───────────────────
                            if extracted:
                                st.markdown('<div class="bs-card-title" style="margin-top:0.8rem">📋 EXTRACTED FIELDS</div>', unsafe_allow_html=True)

                                field_labels = {
                                    "kitta_number":       "किट्टा नं (Kitta)",
                                    "owner_name":         "जग्गाधनी (Owner)",
                                    "citizenship_number": "नागरिकता (Citizenship)",
                                    "land_area_hectares": "क्षेत्रफल (Area ha)",
                                    "land_type":          "जग्गाको किसिम (Type)",
                                    "land_grade":         "श्रेणी (Grade)",
                                    "district":           "जिल्ला (District)",
                                    "ward":               "वडा नं (Ward)",
                                    "has_existing_mortgage": "दित्तल (Mortgage)",
                                }

                                for key, label in field_labels.items():
                                    val = extracted.get(key)
                                    if val is not None and val != "" and val is not False:
                                        display_val = str(val)
                                        st.markdown(f"""
                                        <div class="field-row">
                                          <span class="field-key">{label}</span>
                                          <span class="field-val" style="color:#2D6A4F">✓ {display_val}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"""
                                        <div class="field-row">
                                          <span class="field-key">{label}</span>
                                          <span style="color:#94A3B8; font-size:0.8rem;">not detected</span>
                                        </div>
                                        """, unsafe_allow_html=True)

                                autofill_fields = []
                                if extracted.get("land_area_hectares"):
                                    autofill_fields.append("land area")
                                if extracted.get("land_grade"):
                                    autofill_fields.append("land grade")
                                if extracted.get("district"):
                                    autofill_fields.append("district")
                                if autofill_fields:
                                    st.info(f"💡 Auto-filled from document: {', '.join(autofill_fields)}. Review before submitting.")

                            with st.expander("Raw OCR text"):
                                st.markdown(
                                    f'<div class="ocr-panel">{ocr_result.raw_text}</div>',
                                    unsafe_allow_html=True
                                )

                            st.session_state["ocr_extracted"] = extracted
                            st.session_state["ocr_file_hash"] = file_hash

                    except ImportError:
                        st.warning("OCR modules not available — enter land details manually.")
                        extracted = {}
                    except Exception as e:
                        st.error(f"OCR error: {e}")
                        extracted = {}
            else:
                extracted = st.session_state.get("ocr_extracted", {})
        else:
            st.session_state.pop("ocr_extracted", None)
            st.markdown("""
            <div style="border: 2px dashed #C8C0B0; border-radius: 8px; padding: 1.5rem;
                        text-align: center; color: #94A3B8; font-size: 0.85rem;">
              Drop Lalpurja image here or click to browse<br>
              <span style="font-size: 0.75rem;">Supports JPG, PNG · Fields auto-extracted via EasyOCR</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
       

        # Farmer identity
        st.markdown('<div class="bs-card">', unsafe_allow_html=True)
        st.markdown('<div class="bs-card-title">👤 FARMER IDENTITY</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        farmer_name = c1.text_input("Full Name", value="", placeholder="As on citizenship", key="farmer_name_input")
        citizenship_no = c2.text_input("Citizenship No.", value="", key="citizenship_input")
        c3, c4 = st.columns(2)
        district = c3.selectbox("District", [
            "Kavrepalanchok", "Chitwan", "Dhading", "Surkhet",
            "Karnali", "Jhapa", "Kaski", "Bardiya", "Rupandehi",
            "Sindhupalchok", "Makwanpur", "Palpa", "Gulmi",
        ], key="identity_district_select")
        phone = c4.text_input("Phone", value="98*******", key="phone_input")
        st.markdown('</div>', unsafe_allow_html=True)

        # Land details
        st.markdown('<div class="bs-card">', unsafe_allow_html=True)
        st.markdown('<div class="bs-card-title">🏔️ LAND DETAILS</div>', unsafe_allow_html=True)
        
        ocr = st.session_state.get("ocr_extracted", {})
        c5, c6 = st.columns(2)
        districts = ["Kavrepalanchok", "Chitwan", "Dhading", "Surkhet","Karnali", "Jhapa", "Kaski", "Bardiya", "Rupandehi","Sindhupalchok", "Makwanpur", "Palpa", "Gulmi",]
        ocr_district = ocr.get("district", "")
        district_idx = districts.index(ocr_district) if ocr_district in districts else 0
        district = c5.selectbox("District", districts, index=district_idx, key="district_select")
        land_type_options = ["Khet", "Bari", "Gharbari"]
        ocr_land_type = ocr.get("land_type", "")
        land_type_idx = land_type_options.index(ocr_land_type) if ocr_land_type in land_type_options else 0
        land_type = c6.selectbox("Land Type", land_type_options, index=land_type_idx, key="land_type_select")

        c7, c8 = st.columns(2)
        raw_land_area = ocr.get("land_area_hectares") or 0.1
        try:
             land_area_default = float(raw_land_area)
        except (TypeError, ValueError):
            land_area_default = 0.1     
        raw_land_area = ocr.get("land_area_hectares") or 0.1 
        land_area_default = min(max(float(raw_land_area), 0.001), 5.0)  
        land_area = c7.number_input("Area (hectares)", min_value=0.001, max_value=5.0, value=land_area_default, step=0.0001, key="land_area_input")
        grade_options = ["Aabal", "Doyam", "Sim", "Chahar"]
        ocr_grade = ocr.get("land_grade", "")
        grade_idx = grade_options.index(ocr_grade) if ocr_grade in grade_options else 0
        land_grade = c8.selectbox("Grade", grade_options, index=grade_idx, key="land_grade_select")
        sarkaari_mool = st.number_input("Sarkaari Mool (NRs)", value=0, step=10000, key="sarkaari_mool_input")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="bs-card">', unsafe_allow_html=True)
        st.markdown('<div class="bs-card-title">💰 INCOME SIGNALS</div>', unsafe_allow_html=True)
        coop_income = st.number_input("Cooperative Income (NRs/month)", value=0, step=1000, key="coop_income_input")
        c9, c10 = st.columns(2)
        remittance = c9.number_input("Remittance (NRs/month)", value=0, step=1000, key="remittance_input")
        channel = c10.selectbox("Channel", ["IME", "Prabhu", "Hundi", "None"], key="channel_select")
        hundi_proxy_base = remittance
        if channel == "Hundi":
            st.markdown('<div class="bs-card-title" style="margin-top:0.8rem">📱 HUNDI PROXY SIGNALS</div>', unsafe_allow_html=True)
            proxy_1, proxy_2 = st.columns(2)
            esewa_signal = proxy_1.number_input("eSewa activity (NRs/month)", min_value=0, value=0, step=1000, key="esewa_proxy_input")
            khalti_signal = proxy_2.number_input("Khalti activity (NRs/month)", min_value=0, value=0, step=1000, key="khalti_proxy_input")
            hundi_proxy_base = remittance + esewa_signal + khalti_signal
            st.info(f"Hundi confidence adjustment: I_base NRs {hundi_proxy_base:,.0f} × 0.65 = NRs {hundi_proxy_base * 0.65:,.0f} recognised monthly income.")
        requested_amount = st.number_input("Requested Loan (NRs)", value=0, step=10000, key="requested_amount_input")
        st.markdown('</div>', unsafe_allow_html=True)

        consent = st.checkbox(
            "I consent to BridgeScore accessing land records, cooperative data, and remittance history for credit assessment.",
            value=True,
            key="consent_checkbox",
        )

        use_mock = st.toggle("Use mock pipeline (no backend required)", value=True, key="use_mock_toggle")

        submitted = st.button(
            "▶  Run BridgeScore Pipeline",
            disabled=not consent,
            type="primary",
            key="run_pipeline_button",
            use_container_width=True,
        )

    with col_results:

        if not submitted:
            # placeholder state
            st.markdown("""
            <div style="height: 100%; display: flex; flex-direction: column;
                        align-items: center; justify-content: center;
                        padding: 3rem; text-align: center; color: #94A3B8;">
              <div style="font-size: 3rem; margin-bottom: 1rem;">🌾</div>
              <div style="font-size: 1.1rem; font-weight: 600; color: #374151; margin-bottom: 0.5rem;">
                Ready to assess creditworthiness
              </div>
              <div style="font-size: 0.85rem; max-width: 320px; line-height: 1.6;">
                Fill in the application form and click Run Pipeline to process
                through all 5 BridgeScore agents in real time.
              </div>
            </div>
            """, unsafe_allow_html=True)

        else:
            agents = [
                ("DVA", "Document Verification", "Lalpurja OCR + Malpot cross-check + FSV"),
                ("IIA", "Income Inference",      "Cooperative + remittance aggregation"),
                ("CSA", "Credit Scoring",        "XGBoost inference + SHAP explanation"),
                ("CA",  "Compliance",            "NRB Unified Directive 2081 checks"),
                ("OA",  "Orchestrator",          "Final decision synthesis"),
            ]

            progress_placeholder = st.empty()
            result_placeholder = st.empty()

            with progress_placeholder.container():
                st.markdown('<div class="bs-card">', unsafe_allow_html=True)
                st.markdown('<div class="bs-card-title">⚡ AGENT PIPELINE</div>', unsafe_allow_html=True)
                for i, (code, name, desc) in enumerate(agents):
                    st.markdown(f"""
                    <div class="agent-step">
                      <div class="agent-dot agent-dot-pending">{code}</div>
                      <div class="agent-content">
                        <div class="agent-name">{name} Agent</div>
                        <div class="agent-desc">{desc}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            for complete_index in range(len(agents)):
                with progress_placeholder.container():
                    st.markdown('<div class="bs-card">', unsafe_allow_html=True)
                    st.markdown('<div class="bs-card-title">⚡ AGENT PIPELINE · RUNNING</div>', unsafe_allow_html=True)
                    for index, (code, name, desc) in enumerate(agents):
                        done = index <= complete_index
                        status = "✓ Complete" if done else "Waiting"
                        dot_class = "agent-dot" if done else "agent-dot agent-dot-pending"
                        st.markdown(f'''<div class="agent-step">
                          <div class="{dot_class}">{'✓' if done else code}</div>
                          <div class="agent-content"><div class="agent-name">{name} Agent · {status}</div>
                          <div class="agent-desc">{desc}</div></div></div>''', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                time.sleep(0.12)

            application = {
                "application_id":      f"demo-{int(time.time())}",
                "farmer_name":         farmer_name,
                "district":            district,
                "zone":                "terai" if district in ["Chitwan", "Jhapa", "Bardiya", "Rupandehi"] else "hill",
                "citizenship_number":  citizenship_no,
                "phone_number":        phone,
                "land_area_hectares":  land_area,
                "land_type":           land_type,
                "land_grade":          land_grade,
                "sarkaari_mool_nrs":   sarkaari_mool,
                "coop_income_monthly": coop_income,
                "remittance_monthly":  remittance,
                "hundi_proxy_base_monthly": hundi_proxy_base,
                "remittance_channel":  channel,
                "requested_amount_nrs": requested_amount,
                "lalpurja_image_path": None,
                "_start_time":         time.time(),
            }

            with st.spinner("Running 5-agent pipeline..."):
                pipeline_started = time.perf_counter()
                if use_mock:
                    output = run_mock_pipeline(application)
                else:
                    output = run_pipeline(application)
                elapsed = time.perf_counter() - pipeline_started

            with progress_placeholder.container():
                st.markdown(f'<div class="bs-card"><div class="bs-card-title">⚡ AGENT PIPELINE · COMPLETE IN {elapsed:.1f}s</div>', unsafe_allow_html=True)
                for code, name, desc in agents:
                    st.markdown(f'''<div class="agent-step"><div class="agent-dot">✓</div>
                      <div class="agent-content"><div class="agent-name">{name} Agent · Complete</div>
                      <div class="agent-desc">{desc}</div></div></div>''', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            if not output["success"]:
                st.error(f"Pipeline error: {output['error']}")
            else:
                r = output["result"]
                score = r.get("credit_score", 0)
                decision = r.get("final_decision", "Decline")
                amount = r.get("approved_amount_nrs", 0)

                with result_placeholder.container():

                    css_class = {
                        "Approve":            "decision-approve",
                        "Conditional Approve": "decision-conditional",
                        "Decline":            "decision-decline",
                    }.get(decision, "decision-decline")

                    emoji = {"Approve": "✅", "Conditional Approve": "⚠️", "Decline": "❌"}.get(decision, "❌")

                    st.markdown(f"""
                    <div class="{css_class}">
                      <div class="decision-label">CREDIT DECISION</div>
                      <div class="decision-value">{emoji} {decision}</div>
                      <div class="decision-amount">
                        {"Approved: NRs {:,.0f}".format(amount) if amount > 0 else "Loan not approved"}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                    sc1, sc2 = st.columns([1, 1.5])

                    with sc1:
                        st.markdown('<div class="bs-card">', unsafe_allow_html=True)
                        st.markdown('<div class="bs-card-title">📈 CREDIT SCORE</div>', unsafe_allow_html=True)

                        score_color = APPROVE_COLOR if score >= 65 else (CONDITIONAL_COLOR if score >= 45 else DECLINE_COLOR)
                        pct = score

                        st.markdown(f"""
                        <div class="score-ring-container">
                          <div class="score-ring" style="--score:{pct}; --ring-color:{score_color}">
                            <div class="score-ring-inner"><div>
                              <div class="score-number" style="color:{score_color}">{score:.0f}</div>
                              <div class="score-label">out of 100</div>
                            </div></div>
                          </div>
                          <div style="display:flex; justify-content:space-between; font-size:0.7rem; color:#94A3B8;">
                            <span>Decline &lt;45</span>
                            <span>45–64 Conditional</span>
                            <span>≥65 Approve</span>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)

                        cl = r.get("confidence_lower", score - 5)
                        cu = r.get("confidence_upper", score + 5)
                        st.markdown(f"""
                        <div style="text-align:center; font-size:0.75rem; color:#94A3B8; margin-top:0.5rem;">
                          95% CI: [{cl:.1f} – {cu:.1f}]
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    with sc2:
                        st.markdown('<div class="bs-card">', unsafe_allow_html=True)
                        st.markdown('<div class="bs-card-title">🔍 TOP DECISION FACTORS (SHAP)</div>', unsafe_allow_html=True)

                        factors = r.get("top_shap_factors", [])
                        all_shap = r.get("all_shap_values", {})

                        labels = {
                            "collateral_strength": "Land Collateral",
                            "income_regularity":   "Income Regularity",
                            "income_sufficiency":  "Income Sufficiency",
                            "debt_signal":         "Credit History",
                            "geographic_risk":     "Geographic Risk",
                        }
                        weights = {
                            "collateral_strength": "25%",
                            "income_regularity":   "30%",
                            "income_sufficiency":  "20%",
                            "debt_signal":         "15%",
                            "geographic_risk":     "10%",
                        }
                        max_shap = max(abs(v) for v in all_shap.values()) if all_shap else 1

                        for key, label in labels.items():
                            val = all_shap.get(key, 0)
                            bar_w = int(abs(val) / max_shap * 100)
                            st.markdown(f"""
                            <div class="shap-factor">
                              <div>
                                <div class="shap-label">{label}</div>
                                <div style="font-size:0.7rem;color:#94A3B8">weight {weights[key]}</div>
                              </div>
                              <div class="shap-bar-wrap">
                                <div class="shap-bar-pos" style="width:{bar_w}%;
                                  background:{'#2D6A4F' if val >= 0 else '#C0392B'}"></div>
                              </div>
                              <div class="shap-val">{val:+.2f}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        st.markdown('</div>', unsafe_allow_html=True)

                    # ── FSV + Compliance ───────────────────────────────────────
                    fv1, fv2 = st.columns(2)

                    with fv1:
                        st.markdown('<div class="bs-card">', unsafe_allow_html=True)
                        st.markdown('<div class="bs-card-title">🏔️ COLLATERAL (FSV)</div>', unsafe_allow_html=True)
                        fsv = r.get("fsv_nrs", 0)
                        max_loan_fsv = r.get("max_loan_from_fsv", 0)
                        eff_income = r.get("effective_monthly_income", 0)

                        st.markdown(f"""
                        <div class="field-row">
                          <span class="field-key">Forced Sale Value</span>
                          <span class="field-val">NRs {fsv:,.0f}</span>
                        </div>
                        <div class="field-row">
                          <span class="field-key">Max Loan (60% FSV)</span>
                          <span class="field-val">NRs {max_loan_fsv:,.0f}</span>
                        </div>
                        <div class="field-row">
                          <span class="field-key">FSV Confidence</span>
                          <span class="field-val">{r.get('fsv_confidence', 0):.0%}</span>
                        </div>
                        <div class="field-row">
                          <span class="field-key">Effective Income/mo</span>
                          <span class="field-val">NRs {eff_income:,.0f}</span>
                        </div>
                        <div class="field-row">
                          <span class="field-key">12x Income Capacity</span>
                          <span class="field-val">NRs {eff_income * 12:,.0f}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    with fv2:
                        st.markdown('<div class="bs-card">', unsafe_allow_html=True)
                        st.markdown('<div class="bs-card-title">✅ NRB COMPLIANCE</div>', unsafe_allow_html=True)

                        checks = r.get("compliance_checks", [])
                        for check in checks:
                            icon = "✅" if check["passed"] else "❌"
                            rule = check["rule"].replace("_", " ")
                            st.markdown(f"""
                            <div class="field-row">
                              <span class="field-key">{rule}</span>
                              <span class="{'check-pass' if check['passed'] else 'check-fail'}">{icon}</span>
                            </div>
                            """, unsafe_allow_html=True)

                        fraud_flags = r.get("fraud_flags", [])
                        if fraud_flags:
                            for flag in fraud_flags:
                                st.markdown(f"""
                                <div style="background:#FEF2F2; border-radius:6px; padding:0.4rem 0.6rem;
                                            font-size:0.78rem; color:#C0392B; margin-top:0.3rem;">
                                  ⚠️ {flag}
                                </div>
                                """, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    # ── Conditions / Action items ──────────────────────────────
                    conditions = r.get("conditions", [])
                    action_items = r.get("action_items", [])

                    if conditions:
                        st.markdown('<div class="bs-card">', unsafe_allow_html=True)
                        st.markdown('<div class="bs-card-title">📋 CONDITIONS TO FULFILL</div>', unsafe_allow_html=True)
                        for c in conditions:
                            st.markdown(f"<div style='font-size:0.85rem; padding:0.3rem 0; color:#374151;'>📌 {c}</div>", unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    if action_items and decision == "Decline":
                        st.markdown('<div class="bs-card">', unsafe_allow_html=True)
                        st.markdown('<div class="bs-card-title">🔄 STEPS TO REAPPLY</div>', unsafe_allow_html=True)
                        for item in action_items:
                            st.markdown(f"<div style='font-size:0.85rem; padding:0.3rem 0; color:#374151;'>→ {item}</div>", unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    # ── Nepali SMS ─────────────────────────────────────────────
                    nepali = r.get("nepali_explanation", "")
                    if nepali:
                        st.markdown('<div class="bs-card-title" style="margin-top:0.5rem">📱 NEPALI SMS EXPLANATION</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="nepali-sms">{nepali}</div>', unsafe_allow_html=True)

                    # ── Audit trail ────────────────────────────────────────────
                    with st.expander("🔎 Full Agent Audit Trail", expanded=False):
                        audit = r.get("audit_trail", [])
                        agent_colors = {
                            "DVA": "#2D6A4F", "IIA": "#1D6FA4",
                            "CSA": "#7B2D8B", "CA": "#B7791F", "OA": "#1C2B3A",
                        }
                        for line in audit:
                            prefix = line.split(":")[0] if ":" in line else ""
                            color = agent_colors.get(prefix, "#374151")
                            st.markdown(
                                f'<div style="font-size:0.8rem; padding:0.25rem 0; '
                                f'color:{color}; font-family:monospace;">'
                                f'{"▸ " + line}</div>',
                                unsafe_allow_html=True
                            )

                    # ── Processing time ────────────────────────────────────────
                    proc_time = r.get("processing_time_seconds", 0)
                    st.markdown(f"""
                    <div style="text-align:right; font-size:0.75rem; color:#94A3B8; margin-top:0.5rem;">
                      ⚡ Processed in {proc_time:.1f}s · NRB Unified Directive 2081 compliant
                    </div>
                    """, unsafe_allow_html=True)



with tab2:

    st.markdown('<div class="bs-card-title">📊 SYNTHETIC DATASET EXPLORER — 500 FARMER PROFILES</div>', unsafe_allow_html=True)

    # load synthetic data
    @st.cache_data
    def load_profiles():
        try:
            path = Path(__file__).parent / "data" / "synthetic_training_data.json"
            with open(path) as f:
                data = json.load(f)
            profiles = data["profiles"]
            rows = []
            for p in profiles:
                exp = p.get("expected", {})
                rows.append({
                    "name":       p.get("farmer_name", ""),
                    "district":   p.get("district", ""),
                    "zone":       p.get("zone", "hill"),
                    "land_area":  p["land"]["land_area_hectares"],
                    "land_grade": p["land"]["land_grade"],
                    "land_type":  p["land"]["land_type"],
                    "coop_income":    p["income"]["coop_income_monthly_nrs"],
                    "remittance":     p["income"]["remittance_monthly_nrs"],
                    "hundi":          p["income"]["hundi"],
                    "cib_clean":      p["credit"]["cib_clean"],
                    "score":          exp.get("score", 0),
                    "decision":       exp.get("decision", ""),
                    "fsv":            exp.get("fsv_nrs", 0),
                    "max_loan":       exp.get("max_loan_nrs", 0),
                })
            return pd.DataFrame(rows)
        except Exception as e:
            return None

    df = load_profiles()

    if df is None:
        st.warning("Synthetic training data not found. Run `python -m app.ml.scoring.synthetic_data` first.")
    else:
        # ── Top stats ────────────────────────────────────────────────────────────
        approve_n    = len(df[df["decision"] == "Approve"])
        conditional_n = len(df[df["decision"] == "Conditional Approve"])
        decline_n    = len(df[df["decision"] == "Decline"])
        avg_score    = df["score"].mean()

        s1, s2, s3, s4, s5 = st.columns(5)
        s1.metric("Total Profiles", f"{len(df):,}")
        s2.metric("✅ Approve",            f"{approve_n}",     f"{approve_n/len(df)*100:.0f}%")
        s3.metric("⚠️ Conditional",        f"{conditional_n}", f"{conditional_n/len(df)*100:.0f}%")
        s4.metric("❌ Decline",            f"{decline_n}",     f"{decline_n/len(df)*100:.0f}%")
        s5.metric("Avg Score",             f"{avg_score:.1f}")

        st.divider()

        fc1, fc2, fc3 = st.columns(3)
        zone_filter     = fc1.multiselect("Zone",     ["terai", "hill", "mountain"], default=["terai", "hill", "mountain"], key="zone_filter_multiselect")
        decision_filter = fc2.multiselect("Decision", ["Approve", "Conditional Approve", "Decline"],
                                          default=["Approve", "Conditional Approve", "Decline"], key="decision_filter_multiselect")
        hundi_filter    = fc3.selectbox("Remittance", ["All", "Formal only", "Hundi only"], key="remittance_filter_select")

        filtered = df[df["zone"].isin(zone_filter) & df["decision"].isin(decision_filter)]
        if hundi_filter == "Formal only":
            filtered = filtered[filtered["hundi"] == False]
        elif hundi_filter == "Hundi only":
            filtered = filtered[filtered["hundi"] == True]

        st.caption(f"Showing {len(filtered):,} of {len(df):,} profiles")

        # ── Charts ───────────────────────────────────────────────────────────────
        ch1, ch2 = st.columns(2)

        with ch1:
            st.markdown('<div class="bs-card-title">Score Distribution by Zone</div>', unsafe_allow_html=True)
            chart_data = filtered.groupby(["zone", "decision"]).size().reset_index(name="count")
            zone_score = filtered.groupby("zone")["score"].mean().reset_index()
            zone_score.columns = ["Zone", "Avg Score"]
            st.bar_chart(
                filtered.groupby("zone")["score"].mean(),
                color=ACCENT,
            )

        with ch2:
            st.markdown('<div class="bs-card-title">Decision Breakdown by Zone</div>', unsafe_allow_html=True)
            decision_zone = filtered.groupby(["zone", "decision"]).size().unstack(fill_value=0)
            st.bar_chart(decision_zone)

        ch3, ch4 = st.columns(2)

        with ch3:
            st.markdown('<div class="bs-card-title">Score vs Monthly Income</div>', unsafe_allow_html=True)
            scatter_df = filtered.copy()
            scatter_df["total_income"] = scatter_df["coop_income"] + scatter_df["remittance"]
            scatter_df["total_income_k"] = (scatter_df["total_income"] / 1000).round(1)
            st.scatter_chart(
                scatter_df[["total_income_k", "score"]].rename(
                    columns={"total_income_k": "Monthly Income (NRs 000)", "score": "Score"}
                ),
                x="Monthly Income (NRs 000)",
                y="Score",
                color="#2D6A4F",
            )

        with ch4:
            st.markdown('<div class="bs-card-title">Score vs Land Area</div>', unsafe_allow_html=True)
            st.scatter_chart(
                filtered[["land_area", "score"]].rename(
                    columns={"land_area": "Land Area (ha)", "score": "Score"}
                ),
                x="Land Area (ha)",
                y="Score",
                color="#E9A825",
            )

        # ── Score by grade ────────────────────────────────────────────────────────
        st.markdown('<div class="bs-card-title" style="margin-top:1rem">Average Score by Land Grade</div>', unsafe_allow_html=True)
        grade_score = filtered.groupby("land_grade")["score"].agg(["mean", "count"]).reset_index()
        grade_score.columns = ["Land Grade", "Avg Score", "Count"]
        grade_score["Avg Score"] = grade_score["Avg Score"].round(1)
        st.dataframe(grade_score, use_container_width=True, hide_index=True)

        # ── Hundi impact ────────────────────────────────────────────────────────
        st.markdown('<div class="bs-card-title" style="margin-top:1rem">Hundi vs Formal Remittance Impact</div>', unsafe_allow_html=True)
        hundi_impact = filtered.groupby("hundi")["score"].agg(["mean", "count"]).reset_index()
        hundi_impact["hundi"] = hundi_impact["hundi"].map({True: "Hundi", False: "Formal"})
        hundi_impact.columns = ["Remittance Type", "Avg Score", "Count"]
        hundi_impact["Avg Score"] = hundi_impact["Avg Score"].round(1)
        hundi_impact["Score Penalty"] = (hundi_impact["Avg Score"].max() - hundi_impact["Avg Score"]).round(1)
        st.dataframe(hundi_impact, use_container_width=True, hide_index=True)

        # ── 6 canonical profiles ──────────────────────────────────────────────────
        st.divider()
        st.markdown('<div class="bs-card-title">📌 6 CANONICAL PAPER PROFILES (GROUND TRUTH)</div>', unsafe_allow_html=True)

        canonical = pd.DataFrame([
            {"Farmer": "Ramesh", "District": "Kavrepalanchok", "Zone": "Hill", "Land": "Khet Aabal 0.5ha",
             "Income": "Coop 18k + IME 40k", "Expected Score": 71, "Decision": "Conditional Approve", "Approved": "NRs 1,80,000"},
            {"Farmer": "Sita",   "District": "Dhading",         "Zone": "Hill", "Land": "Bari Doyam 0.3ha",
             "Income": "Coop 9k + Hundi 25k", "Expected Score": 54, "Decision": "Conditional Approve", "Approved": "NRs 65,000"},
            {"Farmer": "Hari",   "District": "Surkhet",         "Zone": "Hill", "Land": "Khet Aabal 1.2ha",
             "Income": "Coop 32k only",        "Expected Score": 63, "Decision": "Approve",             "Approved": "NRs 2,93,000"},
            {"Farmer": "Maya",   "District": "Karnali",         "Zone": "Mountain", "Land": "Bari Sim 0.2ha",
             "Income": "Coop 4.5k + Hundi 12k","Expected Score": 38, "Decision": "Decline",            "Approved": "—"},
            {"Farmer": "Bir",    "District": "Chitwan",         "Zone": "Terai", "Land": "Khet Aabal 0.8ha",
             "Income": "Coop 28k + Prabhu 55k","Expected Score": 84, "Decision": "Approve",            "Approved": "NRs 4,00,000"},
            {"Farmer": "Ganga",  "District": "Dhading",         "Zone": "Hill", "Land": "Bari Doyam 0.4ha",
             "Income": "Coop 7k + IME 30k (irregular)","Expected Score": 49, "Decision": "Decline",   "Approved": "—"},
        ])

        def color_decision(val):
            if val == "Approve":            return "background-color: #D1FAE5; color: #065F46"
            if val == "Conditional Approve": return "background-color: #FEF3C7; color: #92400E"
            if val == "Decline":            return "background-color: #FEE2E2; color: #991B1B"
            return ""

        styled = canonical.style.applymap(color_decision, subset=["Decision"])
        st.dataframe(styled, use_container_width=True, hide_index=True)

        # ── Raw data ─────────────────────────────────────────────────────────────
        with st.expander("View raw profile data"):
            display_cols = ["district", "zone", "land_grade", "coop_income", "remittance", "hundi", "score", "decision"]
            st.dataframe(
                filtered[display_cols].rename(columns={
                    "coop_income": "Coop Income",
                    "remittance":  "Remittance",
                    "hundi":       "Hundi",
                    "score":       "Score",
                    "decision":    "Decision",
                }).head(100),
                use_container_width=True,
                hide_index=True,
            )


with tab3:
    history_head, history_action = st.columns([4, 1])
    with history_head:
        st.markdown('<div class="bs-card-title">🗂️ APPLICATION HISTORY</div>', unsafe_allow_html=True)
        st.caption(f"Live data from {API_BASE_URL}")
    with history_action:
        if st.button("↻ Refresh", key="history_refresh_button", use_container_width=True):
            fetch_application_history.clear()

    applications, history_error = fetch_application_history()
    if history_error:
        st.info("Application history becomes available when the FastAPI service is running.")
        st.caption(history_error)
    elif not applications:
        st.info("No submitted applications yet.")
    else:
        rows = []
        for application in applications:
            decision_data = application.get("decision") or {}
            rows.append({
                "Submitted": application.get("created_at", "—"),
                "Farmer": application.get("farmer_name", "—"),
                "District": application.get("district", "—"),
                "Requested (NRs)": application.get("requested_amount", application.get("requested_amount_nrs", 0)),
                "Status": application.get("status", "pending").title(),
                "Decision": decision_data.get("recommendation", "Pending"),
                "Score": decision_data.get("score", "—"),
                "Approved (NRs)": decision_data.get("approved_amount", "—"),
            })
        history = pd.DataFrame(rows)
        st.dataframe(history, use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(history)} most recent application(s).")


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 2rem 0 1rem; font-size:0.75rem; color:#94A3B8;">
  BridgeScore · Vision Thapa · Global IME Bank CodeFest 2026 · Track A<br>
  Grounded in NRB Unified Directive 2081 · 
  <a href="#" style="color:#2D6A4F; text-decoration:none;">Research Paper</a> ·
  Built with FastAPI · LangGraph · XGBoost · EasyOCR
</div>
""", unsafe_allow_html=True)
