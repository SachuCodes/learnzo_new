"""
Guardian model: links parent users to child learners.
Parents can access dashboards only for learners they are guardians of.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.database import Base


class Guardian(Base):
    """Links parent user to child learner. Parent can view child's analytics only."""
    __tablename__ = "guardians"

    id = Column(Integer, primary_key=True, index=True)
    guardian_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    learner_id = Column(String(64), ForeignKey("learners.learner_id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (UniqueConstraint("guardian_user_id", "learner_id", name="uq_guardian_learner"),)
