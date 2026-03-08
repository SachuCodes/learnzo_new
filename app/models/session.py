from sqlalchemy import Column, String, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.database import Base

class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id = Column(String(36), ForeignKey("learners.learner_id"))
    topic = Column(String(255), nullable=False)
    learning_style = Column(String(1))
    instruction_type = Column(String(50), nullable=True)
    disability_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    # Topic quiz: 0-100 score; correct answers stored for verification
    quiz_score = Column(Float, nullable=True)
    quiz_correct_answers = Column(JSON, nullable=True)  # list of correct option indices per question
    quiz_questions_snapshot = Column(JSON, nullable=True)  # questions + options (no correct index) for idempotent GET

    learner = relationship("Learner")