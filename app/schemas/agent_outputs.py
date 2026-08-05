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




