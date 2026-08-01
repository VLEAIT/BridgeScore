from sqlalchemy import Integer,String,Column,DateTime,ForeignKey,CheckConstraint,text
from sqlalchemy.orm import relationship,Mapped,mapped_column
from datatime import datetime
from sqlalchemy.sql import func
from database import Base,TimeStampMixin
import uuid

class Application(Base,TimeStampMixin,kw_only=True):
    __tablename__ = "applications"

    __table_args__ = (
        CheckConstraint("land_area_hectares > 0",name="check_land_area_hectares_positive"),
        CheckConstraint("coop_income_monthly > 0",name="check_coop_income_monthly_positive"),
        CheckConstraint("remitance_monthly > 0",name="check_remitance_monthly_positive"),
        CheckConstraint("requested_amount > 0",name="check_requested_amount_positive"),
        CheckConstraint("land_type IN ('Khet','Bari','GharBari')",name="ck_application_land_type_valid"),
        CheckConstraint("land_grade IN ('Aabal','Doyam','Sim','Chahar')",name="ck_application_land_grade_valid"),
        CheckConstraint("remittance_channel IN ('IME','Prabhu','Hundi','None')",name="ck_application_remittance_channel_valid"),
        CheckConstraint("application_status IN ('Pending','Processing','Completed','Failed')",name="ck_application_status_valid"),
    )

    id:Mapped[uuid.UUID] = mapped_column(primary_key=True,default_factory=uuid.uuid4,init=False)
    farmer_name:Mapped[str] = mapped_column(String(100),nullable=False,index=True,comment="Name of the farmer same as citizenship name")
    district:Mapped[str] = mapped_column(String(50),nullable=False,index=True,comment="District where land parcel is located")
    land_area_hectares:Mapped[float] = mapped_column(nullable=False,comment="Land area in hectares")
    land_type:Mapped[str] = mapped_column(String(20),nullable=False,comment="Type of land parcel (Khet(irrigated), Bari(rain-fed), GharBari(homestead))")


