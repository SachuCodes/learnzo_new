from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Literal
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.auth.dependencies import get_current_user, get_current_learner, require_role
from app.models.learner import Learner
from app.models.user import User
from app.config import DISABILITY_TYPES

router = APIRouter(prefix="/learners", tags=["learners"])


@router.get("/disability-types")
def list_disability_types():
    """Return exact disability type options for onboarding dropdown."""
    return {"disability_types": list(DISABILITY_TYPES)}

# Exact disability type values for validation
DisabilityType = Literal[
    "adhd", "autism", "dyslexia", "dyspraxia", "dyscalculia",
    "apd", "ocd", "tourette", "intellectual_disability", "spd"
]


class OnboardingRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    # Learnzo is strictly for learners under 18
    age: int = Field(ge=3, le=17, description="Learner age must be between 3 and 17")
    disability_type: DisabilityType


class DisabilityRequest(BaseModel):
    disability_type: str = Field(..., min_length=1)


def _validate_disability_type(value: str) -> str:
    v = value.strip().lower()
    if v not in DISABILITY_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"disability_type must be one of: {list(DISABILITY_TYPES)}"
        )
    return v


@router.post("/onboarding", status_code=201)
def submit_onboarding(
    payload: OnboardingRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("student")),
):
    """Single onboarding: name, age, disability type. Persists and links to authenticated user."""
    learner = db.query(Learner).filter(Learner.user_id == user.id).first()
    if not learner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learner record not found. Register as student first."
        )

    learner.name = payload.name
    learner.age = payload.age
    learner.disability_type = payload.disability_type
    db.commit()
    db.refresh(learner)

    return {
        "learner_id": learner.learner_id,
        "message": "Onboarding completed",
        "name": learner.name,
        "age": learner.age,
        "disability_type": learner.disability_type,
    }


@router.post("", status_code=201)
def create_learner(
    req: OnboardingRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Legacy: create/update learner with name, age, disability (student only). Prefer POST /onboarding."""
    existing = db.query(Learner).filter(Learner.user_id == user.id).first()
    if existing:
        existing.name = req.name
        existing.age = req.age
        existing.disability_type = req.disability_type
        db.commit()
        db.refresh(existing)
        return {"learner_id": existing.learner_id, "message": "Learner profile updated"}

    learner = Learner(
        user_id=user.id,
        name=req.name,
        age=req.age,
        disability_type=req.disability_type,
    )
    db.add(learner)
    db.commit()
    db.refresh(learner)
    return {"learner_id": learner.learner_id, "message": "Learner profile created"}


@router.post("/disability")
def set_disability(
    req: DisabilityRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    learner = db.query(Learner).filter(Learner.user_id == user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    learner.disability_type = _validate_disability_type(req.disability_type)
    db.commit()
    return {"message": "Disability set successfully"}


@router.get("/me")
def get_my_learner_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    learner = db.query(Learner).filter(Learner.user_id == current_user.id).first()
    if not learner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learner profile not found"
        )

    return {
        "learner_id": learner.learner_id,
        "name": learner.name,
        "age": learner.age,
        "disability_type": learner.disability_type,
        "learning_style": learner.learning_style,
        "onboarding_complete": (
            learner.name is not None
            and learner.age is not None
            and learner.disability_type is not None
        ),
        "vark_completed": learner.learning_style is not None,
    }
