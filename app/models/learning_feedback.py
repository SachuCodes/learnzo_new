from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.database import Base

class LearningFeedback(Base):
    __tablename__ = "learning_feedback"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(36), ForeignKey("learning_sessions.id"))
    understanding_level = Column(Integer)  # 1–5
    difficulty = Column(Integer)           # 1–5
    engagement = Column(Integer)            # 1–5
    comments = Column(String(500), nullable=True)
