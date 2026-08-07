from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, Generic, TypeVar
from datetime import datetime

T = TypeVar("T")


class LandType(str, Enum):
    khet = "Khet"
    bari = "Bari"
    gharbari = "GharBari"


class LandGrade(str, Enum):
    aabal = "Aabal"
    doyam = "Doyam"
    sim = "Sim"
    chahar = "Chahar"


class RemittanceChannel(str, Enum):
    ime = "IME"
    prabhu = "Prabhu"
    hundi = "Hundi"
    none = "None"


class ApplicationStatus(str, Enum):
    pending = "Pending"
    processing = "Processing"
    completed = "Completed"
    rejected = "Rejected"


class Recommendation(str, Enum):
    approve = "Approve"
    conditional = "Conditional Approve"
    decline = "Decline"


class AgentName(str, Enum):
    dva = "DVA"
    iia = "IIA"
    csa = "CSA"
    ca = "CA"
    oa = "OA"


class APIResponse(BaseModel, Generic[T]):
    success: bool = Field(..., description="Indicates whether the API request was successful or not.")
    data: Optional[T] = Field(None, description="The data returned by the API request, if any.")
    error: Optional[str] = Field(None, description="An error message, if the API request was not successful.")
    timestamp: datetime = Field(default_factory=datetime.now)
    model_config = {"from_attributes": True}

