# app/services/vark_service.py

from sqlalchemy.orm import Session
from app.models.vark_response import VARKResponse
from pydantic import BaseModel


def get_latest_vark(learner_id: str, db: Session):
    record = (
        db.query(VARKResponse)
        .filter(VARKResponse.learner_id == learner_id)
        .order_by(VARKResponse.created_at.desc())
        .first()
    )

    if not record:
        return None

    return {
        "v_score": record.v_score,
        "a_score": record.a_score,
        "r_score": record.r_score,
        "k_score": record.k_score,
    }
