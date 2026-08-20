#  BridgeScore

**Autonomous Multi-Agent Agricultural Credit Orchestration System for Nepal**

> *"Only 11.7% of Nepal's farm holders receive agricultural credit — despite agriculture sustaining 62% of households."*
> — NSO Agricultural Census 2022

BridgeScore bridges the information gap between creditworthy Nepali farmers and the formal banking system. It processes a Lalpurja photo, cooperative income, and remittance history through a 5-agent AI pipeline and produces an NRB-compliant credit decision in under 60 seconds — without a human loan officer.

---

## The Problem

Consider Ramesh, a farmer in Kavrepalanchok applying for a NRs 2 lakh agricultural loan.

- He owns land — documented in a Lalpurja
- He sells produce through a local cooperative
- His brother sends remittances regularly from Qatar via IME

By any practical measure, Ramesh is creditworthy. But Nepal's traditional banking system cannot see him. It asks for payslips he doesn't have. It queries CIB and finds no record — not because he defaulted, but because he never had a bank loan. It sends a valuator to physically inspect his land, adding days of delay.

**BridgeScore builds the information bridge that currently does not exist.**

---

## System Architecture

```
[ FARMER ]
    │ Lalpurja photo · Cooperative income · Remittance history
    ▼
[ FastAPI Backend ]
    │
    ▼
[ LangGraph Orchestration Pipeline ]
    │
    ├── Agent 1: Document Verification (DVA)
    │     EasyOCR → Lalpurja field extraction
    │     Malpot cross-reference (land registry)
    │     FSV calculation (district multiplier × grade factor × 0.60)
    │
    ├── Agent 2: Income Inference (IIA)
    │     Formal remittance (IME/Prabhu) history
    │     Cooperative sales aggregation
    │     Hundi proxy inference (eSewa/Khalti signals × 0.65 discount)
    │
    ├── Agent 3: Credit Scoring (CSA)
    │     XGBoost on 5 weighted dimensions
    │     SHAP explainability → top 3 decision factors
    │     Score 0–100 with confidence bounds
    │
    ├── Agent 4: Compliance (CA)
    │     NRB Unified Directive 2081 checks
    │     LTV ceiling (60% of FSV)
    │     CIB bureau check
    │     Deprived sector eligibility
    │
    └── Agent 5: Orchestrator (OA)
          Final decision synthesis
          Loan amount calibration
          Nepali-language SMS explanation
          PostgreSQL audit trail

OUTPUT → Approve / Conditional Approve / Decline
         + Nepali explanation + Full audit log
```

---

## Key Nepal-Specific Features

**Forced Sale Value (FSV) Calculator**
Corrects for systematic Sarkaari Mool (government assessed value) undervaluation of 3–5x using district-specific multipliers and land grade factors. Covers all 77 Nepal districts across terai/hill/mountain zones.

**Hundi Inference Engine**
35% confidence discount applied to informal remittance. Proxy signals (eSewa, Khalti, merchant QR, cooperative input purchases) used to corroborate Hundi-sourced income.

**Gulf Gap Tolerance**
Remittance gaps of 1–3 months forgiven — reflects normal end-of-contract return periods for Gulf workers (Qatar, UAE, Saudi Arabia).

**NRB Compliance Layer**
Every decision validated against Nepal Rastra Bank Unified Directive 2081: LTV limits, deprived sector classification, documentation tier adequacy, and CIB bureau checks.

---

## Scoring Dimensions

| Dimension | Weight | Data Source | Nepal Adjustment |
|---|---|---|---|
| Collateral Strength | 25% | Lalpurja OCR + FSV | Mountain/Hill zone discount |
| Income Regularity | 30% | Remittance history | Gulf gap tolerance (3mo) |
| Income Sufficiency | 20% | Coop + remittance | Seasonal harvest alignment |
| Debt Signal | 15% | CIB + existing loans | Microfinance recognized |
| Geographic Risk | 10% | District + land type | Terai lowest risk tier |

**Decision thresholds:** Approve ≥ 65 · Conditional Approve 45–64 · Decline < 45

**Loan ceiling:** `min(60% of FSV, 12× monthly income)`

---

## Validation — 6 Canonical Profiles

Synthetic dataset experiment reproducing scores within ±3 of paper targets:

| Farmer | District | Land | Income | Score | Decision | Approved |
|---|---|---|---|---|---|---|
| Ramesh | Kavrepalanchok | Khet Aabal 0.5ha | Coop 18k + IME 40k | **71** | Conditional Approve | NRs 1,80,000 |
| Sita | Dhading | Bari Doyam 0.3ha | Coop 9k + Hundi 25k | **54** | Conditional Approve | NRs 65,000 |
| Hari | Surkhet | Khet Aabal 1.2ha | Coop 32k only | **63** | Approve | NRs 2,93,000 |
| Maya | Karnali | Bari Sim 0.2ha | Coop 4.5k + Hundi 12k | **38** | Decline | — |
| Bir | Chitwan | Khet Aabal 0.8ha | Coop 28k + Prabhu 55k | **84** | Approve | NRs 4,00,000 |
| Ganga | Dhading | Bari Doyam 0.4ha | Coop 7k + IME 30k (irregular) | **49** | Decline | — |

XGBoost validation: **MAE = 2.39** on held-out synthetic profiles.

---

## Tech Stack

| Component | Technology | Rationale |
|---|---|---|
| Agent Orchestration | LangGraph | Stateful multi-agent workflows with conditional routing |
| Document OCR | EasyOCR | Devanagari/Nepali script extraction |
| Credit Scoring | XGBoost + SHAP | Tabular data performance + interpretable attribution |
| API Backend | FastAPI (Python) | Async, well-suited for agent coordination |
| Database | PostgreSQL (Supabase) | Structured audit trail, NRB compliance-ready |
| Frontend | Streamlit | Live OCR pipeline demo + synthetic profile explorer |
| Infra | Railway | Deployment |

---

## Project Structure

```
bridgescore/
├── app/
│   ├── main.py                    FastAPI entrypoint
│   ├── core/config.py             pydantic-settings
│   ├── api/applications.py        REST endpoints
│   ├── db/
│   │   ├── database.py            SQLAlchemy 2.0 engine
│   │   └── models/                Application, Decision, AuditLog
│   ├── schemas/                   Pydantic schemas + APIResponse[T]
│   ├── agents/
│   │   ├── state.py               LangGraph TypedDict shared state
│   │   ├── graph.py               Pipeline wiring + conditional routing
│   │   ├── document_verification.py  DVA
│   │   ├── income_inference.py       IIA
│   │   ├── credit_scoring.py         CSA
│   │   ├── compliance.py             CA
│   │   └── orchestrator.py           OA
│   ├── ml/
│   │   ├── fsv.py                 FSV calculator (77 districts)
│   │   ├── ocr/paddle_ocr.py      EasyOCR wrapper
│   │   ├── ocr/lalpurja_parser.py Field extractor
│   │   └── scoring/
│   │       ├── features.py        5-dimension feature engineering
│   │       ├── train.py           XGBoost training pipeline
│   │       └── model.py           Inference + SHAP explanation
│   └── integrations/              Mocked: malpot, cib, remittance, nagarik
├── data/
│   ├── district_fsv_multipliers.json   77 districts × zone × tier
│   ├── synthetic_profiles.json         6 canonical anchor profiles
│   └── synthetic_training_data.json    500 training profiles
├── models/
│   ├── model.pkl                  Trained XGBoost model
│   └── shap_explainer.pkl         SHAP TreeExplainer
├── tests/
│   ├── test_fsv_calculator.py
│   └── test_application_schema.py
└── streamlit_app.py               Demo frontend
```

---

## Getting Started

**Prerequisites:** Python 3.12, PostgreSQL (or Supabase account)

```bash
# clone
git clone https://github.com/yourusername/bridgescore.git
cd bridgescore

# environment
python -m venv bridgescore
source bridgescore/bin/activate
pip install -r requirements.txt

# configure
cp .env.example .env
# edit .env with your DATABASE_URL, SECRET_KEY, ANTHROPIC_API_KEY

# database
alembic upgrade head

# train model
python -m scripts.train_model

# run API
uvicorn app.main:app --reload

# run demo frontend
streamlit run streamlit_app.py
```

---

## API Endpoints

```
POST   /api/v1/applications              Submit loan application
GET    /api/v1/applications/{id}         Get application + decision
GET    /api/v1/applications              List applications (paginated)
PATCH  /api/v1/applications/{id}         Update income/amount fields
PATCH  /api/v1/applications/{id}/status  Update pipeline status
POST   /api/v1/applications/{id}/reapply Reapply after decline
```

Interactive docs at `/api/v1/docs` (development mode only).

**Example — Ramesh's application:**

```bash
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -d '{
    "farmer_name": "Ramesh Thapa",
    "district": "Kavrepalanchok",
    "citizenship_number": "12-34-56789",
    "phone_number": "9800000000",
    "land_area_hectares": 0.5,
    "land_type": "Khet",
    "land_grade": "Aabal",
    "coop_income_monthly": 18000,
    "remittance_monthly": 40000,
    "remittance_channel": "IME",
    "requested_amount": 200000,
    "consent_given": true
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "completed",
    "decision": {
      "score": 71.0,
      "recommendation": "Conditional Approve",
      "approved_amount": 180000,
      "top_factors": [
        {"display_label": "Income Regularity", "contribution": 10.5},
        {"display_label": "Land Collateral Strength", "contribution": 9.2},
        {"display_label": "Income Sufficiency", "contribution": 7.8}
      ],
      "nepali_explanation": "तपाईंको आवेदन सर्तसहित स्वीकृत भयो। स्वीकृत ऋण रकम: NRs 1,80,000।"
    }
  }
}
```

---

## Run Tests

```bash
pytest tests/ -v
```

---

## Acknowledged Limitations

- **Synthetic training data** — XGBoost trained on 500 generated profiles. Predictive validity on real borrowers requires a bank partnership providing historical labeled loan outcomes.
- **Malpot digitization** — most rural Nepal districts have paper land records. DVA degrades gracefully but cannot fully automate for undigitized districts.
- **Hundi inference confidence** — 35% discount is conservatively calibrated. Real deployment would recalibrate as outcome data accumulates.
- **No regulatory sandbox** — Nepal has no formal framework for algorithmic lending decisions. Designed for NRB compliance but would require formal approval before live deployment.

---

## Research Foundation

Built on peer-reviewed Nepal-specific research:

- Bhoosal et al. (2025) — *Farmers' Challenges in Securing Agricultural Credit in Nepal*
- Bhattarai (2025) — *Remittance Inflow in Nepal*, KMC Research Journal
- Alliance for Financial Inclusion (2025) — *Alternative Data for Credit Scoring*, 32 jurisdictions
- NRB Unified Directive 2081 (Ekikrit Nirdeshana 2081)
- NSO National Sample Census of Agriculture 2021/22

Full paper: [BridgeScore Research Paper](./bridgescore_paper.pdf)

---

## Author

[***Vision Thapa***](https://www.linkedin.com/in/vision-thapa-4a6608367/)


Built solo in 2 weeks. Stack learned during build: LangGraph, XGBoost, SHAP, EasyOCR.

---

## License

MIT License — see LICENSE file.

> *"BridgeScore does not give farmers access to systems they do not deserve. It ensures systems can recognize the creditworthiness that already exists."*