from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.database import Base


class AssessmentResponse(Base):
    """
    Individual question-level response for a post-learning assessment.

    Each response is mapped to a single VARK modality with an integer weight.
    """

    __tablename__ = "assessment_responses"

    id = Column(Integer, primary_key=True, index=True)

    assessment_id = Column(
        Integer,
        ForeignKey("learning_assessments.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Question identifiers are app-defined; we only need an integer key here.
    question_id = Column(Integer, nullable=False)

    # VARK modality this question contributes to: "V" / "A" / "R" / "K"
    modality = Column(String(1), nullable=False)

    # Non-negative integer weight for this response (e.g. 0, 1, 2)
    weight = Column(Integer, nullable=False, default=1)

