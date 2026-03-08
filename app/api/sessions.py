from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.database import get_db
from app.auth.dependencies import require_role, get_current_user
from app.models.user import User
from app.models.learner import Learner
from app.models.session import LearningSession

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/history")
def get_history(
    user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    learner = db.query(Learner).filter(Learner.user_id == user.id).first()
    if not learner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learner profile not found"
        )
    sessions = (
        db.query(LearningSession)
        .filter(LearningSession.learner_id == learner.learner_id)
        .order_by(desc(LearningSession.created_at))
        .limit(50)
        .all()
    )
    return [
        {
            "id": s.id,
            "topic": s.topic,
            "learning_style": s.learning_style,
            "instruction_type": s.instruction_type,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sessions
    ]