"""
Teacher API — role-based access. Teachers see only assigned students.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.database import get_db
from app.auth.dependencies import require_role
from app.auth.access import can_access_learner, get_accessible_learner_ids
from app.models.user import User
from app.models.learner import Learner
from app.models.vark_response import VARKResponse
from app.models.session import LearningSession
from app.models.interaction import Interaction

from app.services.linucb_engine import load_model, get_engagement_description
from app.services.context_engine import vark_to_context
from app.services.engagement_service import compute_engagement_score

router = APIRouter(prefix="/teacher", tags=["teacher"])


@router.get("/students")
def list_students(
    db: Session = Depends(get_db),
    user: User = Depends(require_role("teacher")),
):
    """List assigned learners (read-only). If no assignments, returns all (backward compat)."""
    learner_ids = get_accessible_learner_ids(user, db)
    q = db.query(Learner).order_by(Learner.learner_id)
    if learner_ids is not None:
        q = q.filter(Learner.learner_id.in_(learner_ids))
    learners = q.all()
    
    results = []
    for l in learners:
        # Get latest VARK for context
        vark = (
            db.query(VARKResponse)
            .filter(VARKResponse.learner_id == l.learner_id)
            .order_by(desc(VARKResponse.created_at))
            .first()
        )
        
        engagement_info = "Data not available"
        if vark:
            model = load_model(l.learner_id)
            current_context = vark_to_context(vark.v_score, vark.a_score, vark.r_score, vark.k_score)
            score = model.get_engagement_score(current_context)
            
            # Get historical engagement trend
            prev_interaction = (
                db.query(Interaction)
                .filter(Interaction.learner_id == l.learner_id, Interaction.ucb_score.isnot(None))
                .order_by(desc(Interaction.created_at))
                .offset(1)
                .first()
            )
            prev_score = prev_interaction.ucb_score if prev_interaction else None
            engagement_info = get_engagement_description(score, prev_score)
            
        results.append({
            "learner_id": l.learner_id,
            "name": l.name,
            "age": l.age,
            "disability_type": l.disability_type,
            "learning_style": l.learning_style,
            "engagement_score": engagement_info,
            "onboarding_complete": (
                l.name is not None and l.age is not None and l.disability_type is not None
            ),
            "vark_completed": l.learning_style is not None,
        })

    return {
        "students": results
    }


@router.get("/students/{learner_id}")
def get_student_detail(
    learner_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("teacher")),
):
    """Single learner: profile, VARK, progress, sessions. Read-only. Must be assigned."""
    if not can_access_learner(user, learner_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    learner = db.query(Learner).filter(Learner.learner_id == learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    vark = (
        db.query(VARKResponse)
        .filter(VARKResponse.learner_id == learner_id)
        .order_by(desc(VARKResponse.created_at))
        .first()
    )
    sessions = (
        db.query(LearningSession)
        .filter(LearningSession.learner_id == learner_id)
        .order_by(desc(LearningSession.created_at))
        .limit(20)
        .all()
    )
    interactions_count = (
        db.query(Interaction).filter(Interaction.learner_id == learner_id).count()
    )

    # Engagement calculation
    engagement_info = "Data not available"
    linucb_stats = None
    engagement_scores = None
    if vark:
        model = load_model(learner_id)
        current_context = vark_to_context(vark.v_score, vark.a_score, vark.r_score, vark.k_score)
        score = model.get_engagement_score(current_context)
        
        # Get historical engagement trend
        prev_interaction = (
            db.query(Interaction)
            .filter(Interaction.learner_id == learner_id, Interaction.ucb_score.isnot(None))
            .order_by(desc(Interaction.created_at))
            .offset(1) # Get the one before the very latest update
            .first()
        )
        prev_score = prev_interaction.ucb_score if prev_interaction else None
        engagement_info = get_engagement_description(score, prev_score)
        
        # Take every parameter (mean rewards per action)
        linucb_stats = model.get_action_scores(current_context)

        # Detailed engagement scores from engagement_service
        engagement_scores = compute_engagement_score(learner_id, db)

    return {
        "learner_id": learner.learner_id,
        "name": learner.name,
        "age": learner.age,
        "disability_type": learner.disability_type,
        "learning_style": learner.learning_style,
        "engagement_score": engagement_info,
        "engagement_scores": engagement_scores,
        "linucb_parameters": linucb_stats,
        "vark_scores": (
            {
                "V": vark.v_score,
                "A": vark.a_score,
                "R": vark.r_score,
                "K": vark.k_score,
            }
            if vark
            else None
        ),
        "sessions_count": len(sessions),
        "interactions_count": interactions_count,
        "recent_sessions": [
            {
                "id": s.id,
                "topic": s.topic,
                "learning_style": s.learning_style,
                "instruction_type": s.instruction_type,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ],
    }


@router.get("/alerts")
def get_all_alerts(
    db: Session = Depends(get_db),
    user: User = Depends(require_role("teacher")),
):
    """Placeholder: teacher alerts. Returns empty until teacher_alerts model exists."""
    return []


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("teacher")),
):
    """Placeholder: resolve alert."""
    return {"status": "resolved"}
