from pydantic import BaseModel,Field,UUID4,field_validator,Annotated,StringConstraints
from typing import Optional,List
from datetime import date,datetime
from schemas.common import LandType,LandGrade,RemittanceChannel,ApplicationStatus
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.decision import DecisionOut


CleanString =Annotated[str,StringConstraints(strip_whitespace=True,min_length=2,max_length=100)]

class ApplicationCreate(BaseModel):
    farmer_name: CleanString
    district: CleanString
    land_area_hectares: float = Field(..., gt=0, description="Land area in hectares")
    land_type: LandType = Field(..., description="Type of the land")
    land_grade: LandGrade = Field(..., description="Grade of the land")
    coop_income_monthly: Decimal = Field(..., ge=0, description="Monthly income from the cooperative")
    remittance_channel: RemittanceChannel = Field(default=RemittanceChannel.none, description="Channel through which remittance is received")
    remittance_monthly:Decimal = Field(default=0.0, ge=0, description="Monthly remittance amount")
    requested_amount: Decimal = Field(..., gt=0, description="Requested amount for the application")
    consent_given: bool = Field(..., description="Indicates whether the farmer has given consent for data processing")

    @field_validator('consent_given')
    @classmethod
    def consent_given_must_not_be_blank(cls, v:bool)->bool:
        if not v:
            raise ValueError('Consent must be given for data processing')
        return v

    @field_validator('farmer_name',mode='before')
    @classmethod
    def farmer_name_must_not_be_blank(cls, v:str)->str:
        if not v.strip():
            raise ValueError('Farmer name must not be blank')
        return v.strip()


    model_config = {
        "json_schema_extra": {
            "example": {
                "farmer_name": "Ramesh Kumar",
                "district": "Kavrepalanchok",
                "land_area_hectares": 0.5, 
                "land_type": "Khet",
                "land_grade": "Aabal",
                "coop_income_monthly": 18000.0,
                "remittance_monthly": 40000.0,
                "remittance_channel": "IME",
                "requested_amount": 200000,
                "consent_given": True
            }
        }
    }    
class ApplicationOut(BaseModel):
    id:UUID4=Field(..., description="Unique identifier for the application")
    farmer_name: CleanString
    district: CleanString
    land_area_hectares: float = Field(..., gt=0, description="Land area in hectares")
    land_type: LandType = Field(..., description="Type of the land")
    land_grade: LandGrade = Field(..., description="Grade of the land")
    coop_income_monthly: Decimal = Field(..., ge=0, description="Monthly income from the cooperative")
    remittance_channel: RemittanceChannel = Field(default=RemittanceChannel.none, description="Channel through which remittance is received")
    remittance_monthly:Decimal = Field(default=0.0, ge=0, description="Monthly remittance amount")
    requested_amount: Decimal = Field(..., gt=0, description="Requested amount for the application")
    status: ApplicationStatus = Field(default=ApplicationStatus.pending, description="Current status of the application")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp when the application was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="Timestamp when the application was last updated")

    decision:Optional["DecisionOut"]=Field(None, description="Decision details if the application has been processed")
    model_config = {"from_attributes": True}

class ApplicationListOut(BaseModel):
    id:UUID4=Field(..., description="Unique identifier for the application")
    farmer_name: CleanString
    district: CleanString
    status: ApplicationStatus = Field(default=ApplicationStatus.pending, description="Current status of the application")
    requested_amount: Decimal = Field(..., gt=0, description="Requested amount for the application")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp when the application was created")
   
    model_config = {"from_attributes": True}   


ApplicationOut.model_rebuild()  





