from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint, Text, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from sqlalchemy.sql import func
from database import Base, CreatedAtMixin
import uuid

VALID_AGENTS=("DVA","IIA","CSA","CA","OA")

class AuditLog(Base,CreatedAtMixin,kw_only=True):
    __tablename__ ="audit_logs"

    __table_args__ = (
        CheckConstraint(f"agent_name IN {VALID_AGENTS}",name="ck_audit_log_agent_name_valid"),
    )

    id:Mapped[uuid.UUID] = mapped_column(primary_key=True,default_factory=uuid.uuid4,init=False)
    application_id:Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id",ondelete="CASCADE"),nullable=False,index=True,comment="Foreign key to the applications table")
    agent_name:Mapped[str]=mapped_column(String(20),nullable=False,index=True,comment="DVA / IIA / CSA / CA / OA")
    input_snapshot:Mapped[dict]=mapped_column(JSON,default_factory=dict,comment="Exact inputs this agent produced — frozen at time of execution")
    output_snapshot:Mapped[dict]=mapped_column(JSON,default_factory=dict,comment="Exact outputs this agent produced — frozen at time of execution")
    notes:Mapped[str]=mapped_column(Text,default="",comment="Any additional notes or comments from the agent")
    application:Mapped["Application"] = relationship("Application",back_populates="audit_logs",init=False)

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} application_id={self.application_id} agent_name={self.agent_name}>"

    


