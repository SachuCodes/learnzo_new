# app/api/learner.py

from fastapi import APIRouter
import numpy as np

from app.services.linucb_engine import load_model, save_model


router = APIRouter(prefix="/learner", tags=["learner"])




@router.get("/learner/state/{learner_id}")
def learner_state(learner_id: str):
    model = load_model(learner_id)

    return {
        "A_trace": [round(float(A.trace()), 4) for A in model.A],
        "b_norm": [round(float(np.linalg.norm(b)), 4) for b in model.b]
    }
