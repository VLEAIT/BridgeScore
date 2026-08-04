from pydantic import BaseModel, Field, UUID4
from typing import Optional, List
from datetime import datetime
from app.schemas.common import Recommendation

class SHAPFactor(BaseModel):
    feature: str=Field(..., description="Feature name e.g. income_regularity")
    contribution: float=Field(..., description="SHAP value-postive pushes towards approval, negative pushes towards rejection")  
    display_label: str=Field(..., description="human readable nepali friendaly label")

class DecisionCreate(BaseModel):
    application_id:UUID4   
    score:float=Field(..., ge=0,le=100)
    recommendation:Recommendation
    approved_amount:float=Field(..., ge=0)
    top_factors:list[SHAPFactor]=Field(default_factory=list, description="Top factors contributing to the decision")
    nepali_expalanation:str=Field(None, min_length=2, description="Nepali explanation for the decision")
    
class DecisionOut(BaseModel):
    id:UUID4
    application_id:UUID4   
    score:float
    recommendation:Recommendation
    approved_amount:float
    top_factors:list[SHAPFactor]
    nepali_expalanation:str
    created_at:datetime

    model_config={"from_attributes":True}
    
