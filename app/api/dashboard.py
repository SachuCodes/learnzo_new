"""
Dashboard API — role-based access (no student access).
- Parents: their child only (via Guardian)
- Teachers: assigned students only (via TeacherStudent)
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.db.database import get_db
from app.auth.dependencies import require_role, get_current_user
from app.auth.access import can_access_learner
from app.models.user import User
from app.models.learner import Learner
from app.models.vark_response import VARKResponse
from app.models.interaction import Interaction

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _ensure_learner_exists(learner_id: str, db: Session) -> Learner:
    learner = db.query(Learner).filter(Learner.learner_id == learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")
    return learner


# --------------------------------------------------
# 1. LEARNER OVERVIEW (teacher/parent/admin)
# --------------------------------------------------
@router.get("/learner/{learner_id}")
def learner_overview(
    learner_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("parent", "teacher", "admin")),
):
    if not can_access_learner(user, learner_id, db):
        raise HTTPException(status_code=403, detail="Access denied")

    _ensure_learner_exists(learner_id, db)

    vark = (
        db.query(VARKResponse)
        .filter(VARKResponse.learner_id == learner_id)
        .order_by(desc(VARKResponse.created_at))
        .first()
    )
    if not vark:
        raise HTTPException(status_code=400, detail="VARK not completed")

    stats = (
        db.query(
            func.count(Interaction.id).label("total_sessions"),
            func.avg(Interaction.reward).label("engagement_score"),
        )
        .filter(Interaction.learner_id == learner_id, Interaction.reward.isnot(None))
        .first()
    )

    return {
        "learner_id": learner_id,
        "vark_preferences": {
            "v_score": vark.v_score,
            "a_score": vark.a_score,
            "r_score": vark.r_score,
            "k_score": vark.k_score,
        },
        "total_sessions": stats.total_sessions or 0,
        "engagement_score": round(float(stats.engagement_score or 0), 2),
    }


# --------------------------------------------------
# 2. LEARNING EFFECTIVENESS (teacher/parent/admin)
# --------------------------------------------------
@router.get("/effectiveness/{learner_id}")
def learning_effectiveness(
    learner_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("parent", "teacher", "admin")),
):
    if not can_access_learner(user, learner_id, db):
        raise HTTPException(status_code=403, detail="Access denied")

    _ensure_learner_exists(learner_id, db)

    rows = (
        db.query(
            Interaction.recommended_instruction,
            func.count(Interaction.id).label("attempts"),
            func.avg(Interaction.reward).label("effectiveness"),
        )
        .filter(Interaction.learner_id == learner_id, Interaction.reward.isnot(None))
        .group_by(Interaction.recommended_instruction)
        .all()
    )
    if not rows:
        raise HTTPException(status_code=400, detail="Not enough data")

    return {
        "learner_id": learner_id,
        "learning_effectiveness": [
            {"modality": r.recommended_instruction, "attempts": r.attempts, "effectiveness": round(float(r.effectiveness), 2)}
            for r in rows
        ],
    }


# --------------------------------------------------
# 3. PROGRESS TIMELINE (teacher/parent/admin)
# --------------------------------------------------
@router.get("/timeline/{learner_id}")
def progress_timeline(
    learner_id: str,
    limit: int = 15,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("parent", "teacher", "admin")),
):
    if not can_access_learner(user, learner_id, db):
        raise HTTPException(status_code=403, detail="Access denied")

    _ensure_learner_exists(learner_id, db)

    rows = (
        db.query(Interaction)
        .filter(Interaction.learner_id == learner_id, Interaction.reward.isnot(None))
        .order_by(desc(Interaction.created_at))
        .limit(limit)
        .all()
    )

    return {
        "learner_id": learner_id,
        "recent_progress": [
            {
                "delivered_instruction": r.delivered_instruction,
                "reward": r.reward,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }
