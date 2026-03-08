"""
TeacherStudent model: links teachers to assigned students.
Teachers can access dashboards only for assigned learners.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.db.database import Base


class TeacherStudent(Base):
    """Links teacher user to assigned learner. Teacher can view learner's analytics."""
    __tablename__ = "teacher_students"

    id = Column(Integer, primary_key=True, index=True)
    teacher_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    learner_id = Column(String(64), ForeignKey("learners.learner_id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (UniqueConstraint("teacher_user_id", "learner_id", name="uq_teacher_student"),)
