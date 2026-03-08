from fastapi import APIRouter
import numpy as np
from app.services.linucb_engine import load_model, INDEX_TO_ACTION

router = APIRouter(prefix="/explain", tags=["explain"])

@router.get("/{learner_id}")
def explain(learner_id: str):
    model = load_model(learner_id)

    explanations = []
    for i, A in enumerate(model.A):
        explanations.append({
            "instruction": INDEX_TO_ACTION[i],
            "confidence": round(float(np.trace(A)), 4)
        })

    return explanations
