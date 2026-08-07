from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import Recommendation, AgentName,NRBRule


class LalpurjaFields(BaseModel):
    kitta_number: Optional[str] = None
    sheet_number: Optional[str] = None
    owner_name: Optional[str] = None
    citizenship_number: Optional[str] = None
    land_area_hectares: Optional[float] = None
    land_type: Optional[str] = None
    land_grade: Optional[str] = None
    district: Optional[str] = None
    ward: Optional[str] = None
    has_existing_mortgage: bool = False


class DVAOutput(BaseModel):
    agent_name: AgentName = AgentName.dva
    lalpurja_verified: bool
    malpot_cross_checked: bool
    lalpurja_field: LalpurjaFields
    fsv_estimate_nrs: float = Field(..., ge=0, description="Forced Sale Value in NRS")
    collateral_confidence: float = Field(..., ge=0, le=1)
    soft_blocks: list[str] = Field(default_factory=list, description="Non-fatal flag e.g. joint family name")
    hard_blocks: list[str] = Field(default_factory=list, description="Fatal flag that stop processing")
    notes: str = " "


class IncomeChannel(BaseModel):
    source: str
    monthly_amount_nrs: float
    confidence: float = Field(..., ge=0, le=1)
    months_of_history: int = 0
    notes: str = ""


class IIAOutput(BaseModel):
    agent_name: AgentName = AgentName.iia
    channels: list[IncomeChannel]
    total_monthly_income_nrs: float
    composite_confidence: float = Field(..., ge=0, le=1)
    seasonal_variability_index: float = Field(..., ge=0, le=1, description="0=stable and 1=highly seasonal")
    hundi_detected: bool
    gulf_gap_applied: bool
    notes: str = " "


class ScoreDimension(BaseModel):
    name: str
    weight: float = Field(..., ge=0, le=1)
    raw_value: float
    weighted_contribution: float
    nepal_adjustment_applied: bool = False
    adjustment_note: str = ""


class CSAOutput(BaseModel):
    agent_name: AgentName = AgentName.csa
    score: float = Field(..., ge=0, le=1)
    recommendation: Recommendation
    dimensions: list[ScoreDimension]
    top_factors: list[dict] = Field(default_factory=list)
    confidence_lower: float
    confidence_upper: float
    notes: str = ""


class ComplianceCheck(BaseModel):
    rule: NRBRule
    passed: bool
    detail: str = " "
    actual_value=float
    threshold_value=float


class CAOutput(BaseModel):
    agent_name: AgentName = AgentName.ca
    all_checks_passed: bool
    checks: list[ComplianceCheck]
    deprived_sector_eligible: bool
    fraud_flags: list[str] = Field(default_factory=list)
    cib_check_completed: bool
    recommended_max_amount_nrs: float
    notes: str = ""


class OAOutput(BaseModel):
    agent_name: AgentName = AgentName.oa
    final_score: float
    final_recommendation: Recommendation
    final_amount_nrs: float
    conditions: list[str] = Field(default_factory=list, description="List of conditions for conditional approvals; empty for approve or decline")
    action_items: list[str] = Field(default_factory=list, description="Actionable steps for decline before reapplying")
    nepali_explanation: str
    processing_time_seconds: float
    notes: str = ""


# minor name error handling
DVAOutout = DVAOutput
CSAoutput = CSAOutput
CAoutput = CAOutput
ScoreDimesion = ScoreDimension

