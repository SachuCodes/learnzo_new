"""
Admin API — link guardians (parent->child) and teacher-student assignments.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.auth.dependencies import require_role
from app.models.user import User
from app.models.learner import Learner
from app.models.guardian import Guardian
from app.models.teacher_student import TeacherStudent

router = APIRouter(prefix="/admin", tags=["admin"])


class GuardianLinkRequest(BaseModel):
    guardian_user_id: int
    learner_id: str


class TeacherAssignmentRequest(BaseModel):
    teacher_user_id: int
    learner_id: str


@router.post("/guardians")
def link_guardian(
    payload: GuardianLinkRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Link parent user to child learner. Parent can then access child's dashboard."""
    learner = db.query(Learner).filter(Learner.learner_id == payload.learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")
    guardian_user = db.query(User).filter(User.id == payload.guardian_user_id).first()
    if not guardian_user or guardian_user.role != "parent":
        raise HTTPException(status_code=400, detail="User must exist and have role 'parent'")
    existing = db.query(Guardian).filter(
        Guardian.guardian_user_id == payload.guardian_user_id,
        Guardian.learner_id == payload.learner_id,
    ).first()
    if existing:
        return {"message": "Already linked", "guardian_user_id": payload.guardian_user_id, "learner_id": payload.learner_id}
    g = Guardian(guardian_user_id=payload.guardian_user_id, learner_id=payload.learner_id)
    db.add(g)
    db.commit()
    return {"message": "Guardian linked", "guardian_user_id": payload.guardian_user_id, "learner_id": payload.learner_id}


@router.post("/teacher-assignments")
def assign_teacher_to_student(
    payload: TeacherAssignmentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Assign teacher to learner. Teacher can then access learner's dashboard."""
    learner = db.query(Learner).filter(Learner.learner_id == payload.learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")
    teacher_user = db.query(User).filter(User.id == payload.teacher_user_id).first()
    if not teacher_user or teacher_user.role != "teacher":
        raise HTTPException(status_code=400, detail="User must exist and have role 'teacher'")
    existing = db.query(TeacherStudent).filter(
        TeacherStudent.teacher_user_id == payload.teacher_user_id,
        TeacherStudent.learner_id == payload.learner_id,
    ).first()
    if existing:
        return {"message": "Already assigned", "teacher_user_id": payload.teacher_user_id, "learner_id": payload.learner_id}
    t = TeacherStudent(teacher_user_id=payload.teacher_user_id, learner_id=payload.learner_id)
    db.add(t)
    db.commit()
    return {"message": "Teacher assigned", "teacher_user_id": payload.teacher_user_id, "learner_id": payload.learner_id}
