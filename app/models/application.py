from sqlalchemy import CheckConstraint, String, Float, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.database import Base, TimeStampMixin
import uuid
from sqlalchemy.dialects.postgresql import JSONB
from typing import Dict,Any,Optional


class Application(Base, TimeStampMixin, kw_only=True):
    __tablename__ = "applications"

    __table_args__ = (
        CheckConstraint("land_area_hectares > 0", name="check_land_area_hectares_positive"),
        CheckConstraint("coop_income_monthly >= 0", name="check_coop_income_monthly_positive"),
        CheckConstraint("remittance_monthly >= 0", name="check_remittance_monthly_positive"),
        CheckConstraint("requested_amount > 0", name="check_requested_amount_positive"),
        CheckConstraint("land_type IN ('Khet','Bari','GharBari')", name="ck_application_land_type_valid"),
        CheckConstraint("land_grade IN ('Aabal','Doyam','Sim','Chahar')", name="ck_application_land_grade_valid"),
        CheckConstraint("remittance_channel IN ('IME','Prabhu','Hundi','None')", name="ck_application_remittance_channel_valid"),
        CheckConstraint("application_status IN ('Pending','Processing','Completed','Rejected')", name="ck_application_status_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default_factory=uuid.uuid4, init=False)
    farmer_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="Name of the farmer same as citizenship name")
    district: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="District where land parcel is located")
    citizenship_number:Mapped[str]=mapped_column(String(50),nullable=False,index=True,comment="Offical citizen number of the applicant")
    phone_number:Mapped[str]=mapped_column(String(15),nullable=False,comment="Contact number for SMS delivery")
    land_area_hectares: Mapped[float] = mapped_column(nullable=False, comment="Land area in hectares")
    land_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="Type of land parcel (Khet(irrigated), Bari(rain-fed), GharBari(homestead))")
    land_grade: Mapped[str] = mapped_column(String(20), nullable=False, comment="Fertility Grade of land parcel (Aabal(1st), Doyam(2nd), Sim(3rd), Chahar(4th))")
    coop_income_monthly: Mapped[float] = mapped_column(Float, nullable=False, comment="Monthly income of the farmer from cooperative farming")
    remittance_monthly: Mapped[Optional[float]] = mapped_column( Float, nullable=True, default=None, comment="Monthly remittance received by the farmer")
    remittance_channel: Mapped[str] = mapped_column(String(20), nullable=False, default="None", comment="Channel through which remittance is received (IME, Prabhu, Hundi, None)")
    requested_amount: Mapped[float] = mapped_column(float, nullable=False, comment="Amount requested by the user in nrs")
    lalpurja_data:Mapped[Optional[Dict[str,Any]]]=mapped_column(JSONB,nullable=True,default=None,comment="Structured fields extracted from lalpurja by DVA-kitta,owner,area,grade")
    lalpurja_image_path:Mapped[Optional[str]]=mapped_column(String(255),nullable=True,default=None,comment="File path of uploaded lalpurja image processed by DVA ")
    consent_given: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="Whether the user has given consent for data processing")
    status: Mapped[str] = mapped_column( String(20), index=True, nullable=False, default="Pending", comment="Status of the application (Pending, Processing, Completed, Rejected)")

    decision: Mapped["Decision"] = relationship("Decision", back_populates="application", uselist=False, init=False, cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="application", init=False, order_by="AuditLog.created_at", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Application id={self.id} farmer={self.farmer_name} status={self.status}>"

