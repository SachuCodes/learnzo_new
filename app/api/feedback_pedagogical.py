from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.session import LearningSession
from app.models.learning_feedback import LearningFeedback
from app.auth.dependencies import require_role
from app.services.logging_service import log_session_summary
from app.services.engagement_service import compute_engagement_score
from app.models.learner import Learner

router = APIRouter(prefix="/feedback/pedagogical", tags=["feedback"])

class PedagogicalFeedback(BaseModel):
    session_id: str
    understanding: int  # 1–5
    difficulty: int     # 1–5
    engagement: int     # 1–5
    comments: str | None = None

@router.post("")
def submit_pedagogical_feedback(
    req: PedagogicalFeedback,
    db: Session = Depends(get_db),
    user=Depends(require_role("student"))
):
    session = db.query(LearningSession).filter(
        LearningSession.id == req.session_id
    ).first()

    if not session:
        raise HTTPException(404, "Session not found")

    feedback = LearningFeedback(
        session_id=req.session_id,
        understanding_level=req.understanding,
        difficulty=req.difficulty,
        engagement=req.engagement,
        comments=req.comments
    )

    db.add(feedback)
    db.commit()

    # Log summary of quick check (pedagogical feedback)
    try:
        learner = db.query(Learner).filter(Learner.user_id == user.id).first()
        if learner:
            engagement_data = compute_engagement_score(learner.learner_id, db)
            log_session_summary(
                learner_id=learner.learner_id,
                session_id=req.session_id,
                event_type="quick_check_submitted",
                data={
                    "understanding": req.understanding,
                    "difficulty": req.difficulty,
                    "engagement": req.engagement,
                    "comments": req.comments,
                    "current_mode": learner.learning_style,
                    "average_engagement_score": engagement_data.get("overall_score", 0.0)
                }
            )
    except Exception:
        pass  # Non-critical

    return {"message": "Pedagogical feedback saved"}
