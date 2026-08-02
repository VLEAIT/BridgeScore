from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base,Mapped,MappedAsDataclass
from datatime import datetime,timezone
from sqlalchemy.sql import func
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  

class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(Datetime(timezone=True),server_default=func.now(), nullable=False,init=False)

class TimeStampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(Datetime(timezone=True),server_default=func.now(), onupdate=func.now(), nullable=False,init=False)
   

class Base(MappedAsDataclass, declarative_base,kw_only=True):
    pass
   
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()