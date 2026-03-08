from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Literal, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.database import get_db
from app.auth.dependencies import require_role
from app.models.user import User
from app.models.learner import Learner
from app.models.session import LearningSession
from app.models.vark_response import VARKResponse
from app.models.learning_assessment import LearningAssessment
from app.models.assessment_response import AssessmentResponse
from app.services.vark_engine import get_dominant_style
from app.services.logging_service import log_session_summary
from app.services.engagement_service import compute_engagement_score

router = APIRouter(prefix="/assessments", tags=["assessments"])


class AssessmentItem(BaseModel):
    question_id: int = Field(..., ge=1)
    modality: Literal["V", "A", "R", "K"]
    weight: int = Field(1, ge=0, le=5, description="Non-negative integer contribution to the modality")


class AssessmentSubmitRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    items: List[AssessmentItem] = Field(..., min_length=1, description="Per-question assessment responses")


@router.post("", status_code=201)
def submit_assessment(
    payload: AssessmentSubmitRequest,
    user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    """
    Submit a post-learning assessment for a completed topic/session.

    - Each item is mapped to a VARK modality with a non-negative integer weight.
    - The deltas are applied incrementally to the learner's existing VARK scores.
    - A new VARKResponse row is created with updated totals.
    """
    learner = db.query(Learner).filter(Learner.user_id == user.id).first()
    if not learner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learner profile not found",
        )

    session = (
        db.query(LearningSession)
        .filter(
            LearningSession.id == payload.session_id,
            LearningSession.learner_id == learner.learner_id,
        )
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session for learner",
        )

    # Aggregate VARK deltas for this assessment
    deltas: Dict[str, int] = {"V": 0, "A": 0, "R": 0, "K": 0}
    for item in payload.items:
        deltas[item.modality] += int(item.weight)

    # Persist assessment summary
    assessment = LearningAssessment(
        learner_id=learner.learner_id,
        session_id=session.id,
        topic=session.topic,
        delta_v=deltas["V"],
        delta_a=deltas["A"],
        delta_r=deltas["R"],
        delta_k=deltas["K"],
    )
    db.add(assessment)
    db.flush()  # assign ID for responses

    # Persist per-question responses
    for item in payload.items:
        db.add(
            AssessmentResponse(
                assessment_id=assessment.id,
                question_id=item.question_id,
                modality=item.modality,
                weight=int(item.weight),
            )
        )

    # Fetch latest VARK scores (baseline)
    latest = (
        db.query(VARKResponse)
        .filter(VARKResponse.learner_id == learner.learner_id)
        .order_by(desc(VARKResponse.created_at))
        .first()
    )

    base_v = latest.v_score if latest and latest.v_score is not None else 0
    base_a = latest.a_score if latest and latest.a_score is not None else 0
    base_r = latest.r_score if latest and latest.r_score is not None else 0
    base_k = latest.k_score if latest and latest.k_score is not None else 0

    new_v = base_v + deltas["V"]
    new_a = base_a + deltas["A"]
    new_r = base_r + deltas["R"]
    new_k = base_k + deltas["K"]

    # Create a new VARKResponse snapshot with updated totals
    vark_entry = VARKResponse(
        learner_id=learner.learner_id,
        v_score=new_v,
        a_score=new_a,
        r_score=new_r,
        k_score=new_k,
    )
    db.add(vark_entry)

    # Update learner's dominant learning_style based on updated totals
    updated_scores = {"V": new_v, "A": new_a, "R": new_r, "K": new_k}
    dominant = get_dominant_style(updated_scores)
    learner.learning_style = dominant

    db.commit()
    db.refresh(vark_entry)

    # Log summary of quiz submission
    try:
        engagement_data = compute_engagement_score(learner.learner_id, db)
        log_session_summary(
            learner_id=learner.learner_id,
            session_id=session.id,
            event_type="quiz_submitted",
            data={
                "topic": session.topic,
                "deltas": deltas,
                "vark_scores": updated_scores,
                "learning_style": dominant,
                "current_mode": dominant,  # Added as current mode
                "average_engagement_score": engagement_data.get("overall_score", 0.0)
            }
        )
    except Exception:
        pass  # Non-critical: don't fail the response if logging fails

    return {
        "learner_id": learner.learner_id,
        "session_id": session.id,
        "topic": session.topic,
        "deltas": deltas,
        "vark_scores": {
            "V": new_v,
            "A": new_a,
            "R": new_r,
            "K": new_k,
        },
        "learning_style": dominant,
        "updated_at": vark_entry.created_at.isoformat() if vark_entry.created_at else None,
    }

