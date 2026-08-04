from datetime import datetime
from pydantic import BaseModel, UUID4
from app.schemas.common import AgentName


class AuditLogOut(BaseModel):
    id: UUID4
    application_id: UUID4
    agent_name: AgentName
    input_snapshot: dict
    output_snapshot: dict
    notes: str
    created_at: datetime

    model_config = {"from_attributes": True}

