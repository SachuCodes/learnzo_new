# app/api/debug.py

from fastapi import APIRouter, HTTPException
import numpy as np

from app.services.linucb_engine import load_model, ACTIONS

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/linucb/{learner_id}")
def inspect_linucb(learner_id: str):
    model = load_model(learner_id)

    result = {}

    for i, action in enumerate(ACTIONS):
        A_inv = np.linalg.inv(model.A[i])
        theta = A_inv @ model.b[i]

        mean = float(np.linalg.norm(theta))
        uncertainty = float(np.trace(A_inv))

        result[action] = {
            "mean_strength": round(mean, 4),
            "uncertainty": round(uncertainty, 4)
        }

    best_action = max(result, key=lambda x: result[x]["mean_strength"])

    return {
        "actions": result,
        "current_best_action": best_action
    }
