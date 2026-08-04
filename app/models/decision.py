from sqlalchemy import CheckConstraint, String, Float, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from sqlalchemy.sql import func
from database import Base, CreatedAtMixin
import uuid

class Decision(Base,CreatedAtMixin,kw_only=True):
    __tablename__ = "decisions"

    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="ck_decision_score_range"),
        CheckConstraint("approved_amount >= 0", name="ck_decision_approved_amount_non_negative"),
        CheckConstraint("declined_amount >= 0", name="ck_decision_declined_amount_non_negative"),
        CheckConstraint("recommendation IN ('approve','conditional_approve','decline')", name="ck_decision_recommendation_valid")
        )

    id:Mapped[uuid.UUID] = mapped_column(primary_key=True,default_factory=uuid.uuid4,init=False)
    application_id:Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id",ondelete="CASCADE"),nullable=False,index=True,unique=True,comment="Foreign key to the applications table")
    score:Mapped[float] = mapped_column(Float,nullable=False,comment="BridgeScore 0-100:>=65 approved, 45-64 conditional approve, <45 decline")
    recommendation:Mapped[str] = mapped_column(String(30),nullable=False,comment="Recommendation based on the score (approve, conditional_approve, decline)")
    approved_amount:Mapped[float] = mapped_column(Float,nullable=False,comment="Calibrated loan amount in NRs — may differ from requested_amount")
    top_factors:Mapped[dict] = mapped_column(JSON,default_factory=dict,comment="Top 3 SHAP feature contributions — populated in Phase 4 ")
    nepali_explanation:Mapped[str]=mapped_column(Text,nullable=False,comment="Plain Nepali explanation delivered via SMS and portal")
    application:Mapped["Application"] = relationship("Application",back_populates="decision",init=False)

    def __repr__(self) -> str:
        return f"<Decision id={self.id} application_id={self.application_id} score={self.score} recommendation={self.recommendation}>"




