from pydantic import BaseModel,Field,UUID4,field_validator
from typing import Optional,List
from datetime import date,datetime
from schemas.common import LandType,LandGrade,RemittanceChannel,ApplicationStatus

class ApplicationCreate(BaseModel):
    farmer_name: str = Field(..., min_length=2, max_length=100, description="Name of the farmer")
    district: str = Field(..., min_length=2, max_length=100, description="District of the farmer")
    land_area_hectares: float = Field(..., gt=0, description="Land area in hectares")
    land_type: LandType = Field(..., description="Type of the land")
    land_grade: LandGrade = Field(..., description="Grade of the land")
    coop_income_monthly: float = Field(..., ge=0, description="Monthly income from the cooperative")
    remittance_channel: RemittanceChannel = Field(default=RemittanceChannel.none, description="Channel through which remittance is received")
    requested_amount: float = Field(..., gt=0, description="Requested amount for the application")
    consent_given: bool = Field(..., description="Indicates whether the farmer has given consent for data processing")

    @field_validator('consent_given')
    @classmethod
    def consent_given_must_not_be_blank(cls, v:bool)->bool:
        if not v:
            raise ValueError('Consent must be given for data processing')
        return v


        





