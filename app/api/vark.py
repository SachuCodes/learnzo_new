from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Literal
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.auth.dependencies import require_role
from app.models.learner import Learner
from app.models.vark_response import VARKResponse
from app.services.vark_questions import get_vark_questions_list
from app.services.vark_engine import score_vark_yes_no, get_dominant_style

router = APIRouter(prefix="/vark", tags=["vark"])

# ---------- Schemas ----------

class VarkAnswerItem(BaseModel):
    question_id: int = Field(..., ge=1, le=20)
    answer: Literal["yes", "no"]


class VarkSubmitRequest(BaseModel):
    responses: List[VarkAnswerItem] = Field(..., min_length=20, max_length=20)


# ---------- Endpoints ----------

@router.get("/questions")
def get_vark_questions():
    """Return 20 Yes/No questions (5 Visual, 5 Auditory, 5 Reading/Writing, 5 Kinesthetic)."""
    return {"questions": get_vark_questions_list()}


@router.post("/submit")
def submit_vark(
    data: VarkSubmitRequest,
    user=Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    learner = db.query(Learner).filter(Learner.user_id == user.id).first()
    if not learner:
        raise HTTPException(status_code=403, detail="Learner profile not found")

    if not learner.disability_type:
        raise HTTPException(
            status_code=400,
            detail="Complete onboarding (name, age, disability type) before VARK"
        )

    # Validate we have exactly one answer per question 1-20
    qids = {r.question_id for r in data.responses}
    if qids != set(range(1, 21)):
        raise HTTPException(
            status_code=400,
            detail="Must provide exactly one answer for each question 1-20"
        )

    responses_dict = [{"question_id": r.question_id, "answer": r.answer} for r in data.responses]
    scores = score_vark_yes_no(responses_dict, disability_type=learner.disability_type)
    dominant = get_dominant_style(scores)

    vark_entry = VARKResponse(
        learner_id=learner.learner_id,
        v_score=scores["V"],
        a_score=scores["A"],
        r_score=scores["R"],
        k_score=scores["K"],
    )
    db.add(vark_entry)
    learner.learning_style = dominant
    db.commit()
    db.refresh(learner)

    return {
        "status": "submitted",
        "scores": scores,
        "learning_style": dominant,
    }


@router.get("/result")
def get_vark_result(
    user=Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    learner = db.query(Learner).filter(Learner.user_id == user.id).first()
    if not learner or not learner.learning_style:
        raise HTTPException(status_code=404, detail="VARK not completed")

    latest = (
        db.query(VARKResponse)
        .filter(VARKResponse.learner_id == learner.learner_id)
        .order_by(VARKResponse.created_at.desc())
        .first()
    )
    result = {
        "learning_style": learner.learning_style,
    }
    if latest:
        result["scores"] = {
            "V": latest.v_score,
            "A": latest.a_score,
            "R": latest.r_score,
            "K": latest.k_score,
        }
    return result