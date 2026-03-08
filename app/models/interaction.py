from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.database import Base

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id = Column(String(36), ForeignKey("learners.learner_id"), nullable=False)
    session_id = Column(String(36), ForeignKey("learning_sessions.id"), nullable=False)
    context = Column(JSON, nullable=True)
    recommended_instruction = Column(String(50), nullable=True)
    delivered_instruction = Column(String(50), nullable=True)
    reward = Column(Integer, nullable=True)  # -1, 0, 1
    ucb_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    learner = relationship("Learner")
    session = relationship("LearningSession")
