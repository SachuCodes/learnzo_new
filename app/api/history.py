from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.database import get_db
from app.auth.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.learner import Learner
from app.models.interaction import Interaction

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/{learner_id}")
def get_learner_history(
    learner_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("student", "teacher", "parent", "admin")),
):
    if user.role == "student":
        learner = db.query(Learner).filter(Learner.user_id == user.id).first()
        if not learner or learner.learner_id != learner_id:
            raise HTTPException(status_code=403, detail="Access denied")

    rows = (
        db.query(Interaction)
        .filter(Interaction.learner_id == learner_id)
        .order_by(desc(Interaction.created_at))
        .limit(limit)
        .all()
    )

    history = [
        {
            "id": r.id,
            "context": r.context,
            "recommended_instruction": r.recommended_instruction,
            "delivered_instruction": r.delivered_instruction,
            "reward": r.reward,
            "ucb_score": r.ucb_score,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]

    return {
        "learner_id": learner_id,
        "count": len(history),
        "history": history,
    }
