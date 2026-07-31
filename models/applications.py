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
    )


