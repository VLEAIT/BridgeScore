from pydantic import BaseModel,Field
from typing import Optional
from app.schemas.common import Recommendation,AgentName



class LalpurjaFields(BaseModel):
    kitta_number:Optional[str]=None
    sheet_number:Optional[str]=None
    owner_name:Optional[str]=None
    citizenship_number:Optional[str]=None
    land_area_hectors:Optional[float]=None
    land_type:Optional[str]=None
    land_grade:Optional[str]=None
    district:Optional[str]=None
    ward:Optional[str]=None
    has_existing_mortgage:bool=False

class DVAOutout(BaseModel):
    agent_name:AgentName=AgentName.dva
    lalpurja_verified:bool
    malpot_cross_checked:bool
    lalpurja_field:LalpurjaFields
    fsv_estimate_nrs:float=Field(...,ge=0,description="Forced Sale Value in NRS")
    collateral_confiedence:float=Field(...,ge=0,le=1)
    soft_blocks:list[str]=Field(default_factory=list,description="Non-fatal flag e.g. joint family name")
    hard_blocks:list[str]=Field(default_factory=list,description="Fatal flag that stop  processing")
    notes:str=" "


class IncomeChannel(BaseModel):
    source:str
    monthly_amount_nrs:float
    confidence:float=Field(...,ge=0,le=1)
    months_of_history:int=0
    notes:str=""

class IIAOutput(BaseModel):
    agent_name:AgentName=AgentName.iia
    channels:list[IncomeChannel]
    total_monthly_income_nrs:float
    composite_confidence:float=Field(..., ge=0,le=1)
    seasonal_varablility_index:float=Field(...,ge=0,le=1,description="0=stable and 1=highly seasonal")
    hundi_detected:bool
    gulf_gap_applied:bool
    notes:str=" "
    

    


