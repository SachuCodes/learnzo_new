from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class VARKResponse(Base):
    __tablename__ = "vark_responses"

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(String(64), index=True)

    v_score = Column(Integer)
    a_score = Column(Integer)
    r_score = Column(Integer)
    k_score = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
