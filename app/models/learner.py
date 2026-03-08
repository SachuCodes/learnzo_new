import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Learner(Base):
    __tablename__ = "learners"

    learner_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    name = Column(String(100), nullable=True)   # Set on onboarding
    age = Column(Integer, nullable=True)        # Set on onboarding

    # 🔥 THIS WAS MISSING
    learning_style = Column(String(1), nullable=True)  # V / A / R / K
    disability_type = Column(String(50), nullable=True)
 # e.g., "dyslexia", "visual_impairment"

    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )

    user = relationship(
        "User",
        back_populates="learner"
    )
