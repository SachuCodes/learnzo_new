from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class LearningAssessment(Base):
    """
    Post-learning assessment summary for a single learning session/topic.

    Stores per-assessment VARK deltas that are applied incrementally on top
    of the baseline VARK questionnaire.
    """

    __tablename__ = "learning_assessments"

    id = Column(Integer, primary_key=True, index=True)

    # Learner and session linkage
    learner_id = Column(String(36), ForeignKey("learners.learner_id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(36), ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=False)

    # Cached topic for easier reporting
    topic = Column(String(255), nullable=False)

    # Incremental VARK contribution from this assessment (non-negative integers)
    delta_v = Column(Integer, nullable=False, default=0)
    delta_a = Column(Integer, nullable=False, default=0)
    delta_r = Column(Integer, nullable=False, default=0)
    delta_k = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

