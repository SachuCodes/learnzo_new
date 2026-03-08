"""
Role-based access control for dashboards and analytics.
- Students: NEVER access dashboards, charts, or analytics
- Parents: Access dashboards for their child only (via Guardian)
- Teachers: Access dashboards for assigned students (via TeacherStudent)
"""
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.guardian import Guardian
from app.models.teacher_student import TeacherStudent


def can_access_learner(user: User, learner_id: str, db: Session) -> bool:
    """
    Check if user can access learner's data.
    - Admin: always
    - Parent: only if Guardian(user_id, learner_id) exists
    - Teacher: only if TeacherStudent(user_id, learner_id) exists, OR no assignments (backward compat)
    """
    if user.role == "admin":
        return True
    if user.role == "parent":
        g = db.query(Guardian).filter(
            Guardian.guardian_user_id == user.id,
            Guardian.learner_id == learner_id,
        ).first()
        return g is not None
    if user.role == "teacher":
        assigned = db.query(TeacherStudent).filter(
            TeacherStudent.teacher_user_id == user.id,
            TeacherStudent.learner_id == learner_id,
        ).first()
        if assigned:
            return True
        # Backward compat: if teacher has no assignments, allow access to all
        any_assignment = db.query(TeacherStudent).filter(TeacherStudent.teacher_user_id == user.id).first()
        return any_assignment is None
    return False


def get_accessible_learner_ids(user: User, db: Session) -> list | None:
    """
    Get list of learner_ids user can access. Returns None if access to all (teacher with no assignments).
    """
    if user.role == "admin":
        return None  # all
    if user.role == "parent":
        guardians = db.query(Guardian).filter(Guardian.guardian_user_id == user.id).all()
        return [g.learner_id for g in guardians]
    if user.role == "teacher":
        assignments = db.query(TeacherStudent).filter(TeacherStudent.teacher_user_id == user.id).all()
        if not assignments:
            return None  # backward compat: all learners
        return [a.learner_id for a in assignments]
    return []
