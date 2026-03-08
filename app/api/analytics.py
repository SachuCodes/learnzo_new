"""
Analytics API — role-based access (no student access).
- Students: 403
- Parents: their child only (via Guardian)
- Teachers: assigned students only (via TeacherStudent)
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.database import get_db
from app.auth.dependencies import require_role, get_current_user
from app.auth.access import can_access_learner, get_accessible_learner_ids
from app.models.user import User
from app.models.learner import Learner
from app.models.vark_response import VARKResponse
from app.services.engagement_service import compute_engagement_score, get_aggregate_engagement_for_teacher

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/engagement/aggregate")
def get_aggregate_engagement(
    lookback_days: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("teacher", "admin")),
):
    """Get aggregate engagement for teacher's assigned students (or all if no assignments)."""
    learner_ids = get_accessible_learner_ids(user, db)
    data = get_aggregate_engagement_for_teacher(db, lookback_days, learner_ids)
    return data


@router.get("/engagement/{learner_id}")
def get_learner_engagement(
    learner_id: str,
    lookback_days: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("teacher", "parent", "admin")),
):
    """Get engagement score for a specific learner. Students never have access."""
    if not can_access_learner(user, learner_id, db):
        raise HTTPException(status_code=403, detail="Access denied")

    learner_obj = db.query(Learner).filter(Learner.learner_id == learner_id).first()
    if not learner_obj:
        raise HTTPException(status_code=404, detail="Learner not found")

    score_data = compute_engagement_score(learner_id, db, lookback_days)
    return {
        "learner_id": learner_id,
        "learner_name": learner_obj.name,
        **score_data,
    }


# ---------- VARK SCORE APIs ----------


@router.get("/vark/{learner_id}")
def get_learner_vark_scores(
    learner_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("teacher", "parent", "admin")),
):
    """Get individual VARK scores for a learner. Students never have access."""
    if not can_access_learner(user, learner_id, db):
        raise HTTPException(status_code=403, detail="Access denied")

    learner_obj = db.query(Learner).filter(Learner.learner_id == learner_id).first()
    if not learner_obj:
        raise HTTPException(status_code=404, detail="Learner not found")

    latest = (
        db.query(VARKResponse)
        .filter(VARKResponse.learner_id == learner_id)
        .order_by(desc(VARKResponse.created_at))
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="VARK not completed for this learner")

    return {
        "learner_id": learner_id,
        "learner_name": learner_obj.name,
        "learning_style": learner_obj.learning_style,
        "vark_scores": {
            "V": latest.v_score or 0,
            "A": latest.a_score or 0,
            "R": latest.r_score or 0,
            "K": latest.k_score or 0,
        },
        "updated_at": latest.created_at.isoformat() if latest.created_at else None,
    }


@router.get("/vark/aggregate/distribution")
def get_vark_distribution(
    db: Session = Depends(get_db),
    user: User = Depends(require_role("teacher", "admin")),
):
    """
    Get aggregated VARK distribution for teacher's assigned students.
    Returns counts of dominant learning styles (V, A, R, K) and per-student scores.
    """
    learner_ids = get_accessible_learner_ids(user, db)
    q = db.query(Learner).filter(Learner.learning_style.isnot(None))
    if learner_ids is not None:
        q = q.filter(Learner.learner_id.in_(learner_ids))
    learners = q.all()

    distribution = {"V": 0, "A": 0, "R": 0, "K": 0}
    students_vark = []

    for learner in learners:
        latest = (
            db.query(VARKResponse)
            .filter(VARKResponse.learner_id == learner.learner_id)
            .order_by(desc(VARKResponse.created_at))
            .first()
        )
        if latest and learner.learning_style:
            distribution[learner.learning_style] = distribution.get(learner.learning_style, 0) + 1
            students_vark.append({
                "learner_id": learner.learner_id,
                "name": learner.name or "Unknown",
                "learning_style": learner.learning_style,
                "vark_scores": {
                    "V": latest.v_score or 0,
                    "A": latest.a_score or 0,
                    "R": latest.r_score or 0,
                    "K": latest.k_score or 0,
                },
            })

    return {
        "total_students": len(learners),
        "vark_distribution": distribution,
        "students": students_vark,
    }
