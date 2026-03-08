# app/api/feedback.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import numpy as np
import json

from app.services.alert_engine import evaluate_alerts
from app.services.linucb_engine import load_model, save_model, ACTION_TO_INDEX, INDEX_TO_ACTION
from app.services.vark_service import get_latest_vark
from app.services.context_engine import vark_to_context
from app.services.logging_service import ensure_learner_exists
from app.db.database import get_db
from app.auth.dependencies import require_role, get_current_user
from app.models.session import LearningSession
from app.models.interaction import Interaction

router = APIRouter(prefix="/feedback/rl", tags=["feedback-rl"])


class FeedbackRequest(BaseModel):
    session_id: str
    reward: int  # -1, 0, 1


@router.post("/", dependencies=[Depends(require_role("student"))])
def submit_feedback(
    req: FeedbackRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    learner_id = user.learner.learner_id if user.learner else None
    if not learner_id:
        raise HTTPException(403, "Student not linked to learner")

    if req.reward not in (-1, 0, 1):
        raise HTTPException(400, "Reward must be -1, 0, or 1")

    ensure_learner_exists(learner_id, db)

    # Fetch the session to get the instruction type
    session = db.query(LearningSession).filter(
        LearningSession.id == req.session_id
    ).first()
    
    if not session:
        raise HTTPException(400, "Session not found")

    # Update Interaction record with reward
    interaction = db.query(Interaction).filter(
        Interaction.session_id == req.session_id
    ).first()
    
    if interaction:
        interaction.reward = req.reward
        interaction.delivered_instruction = session.instruction_type
        
        # Load model to get current context and calculate ucb_score for this interaction
        model = load_model(learner_id)
        vark = get_latest_vark(learner_id, db)
        if vark:
            ctx_list = vark_to_context(vark["v_score"], vark["a_score"], vark["r_score"], vark["k_score"])
        else:
            ctx_list = [1.0, 0.0, 0.0, 0.0]
        
        context = np.array(ctx_list)
        action_index = ACTION_TO_INDEX.get(session.instruction_type, 0)
        
        # Calculate engagement score for this interaction
        interaction.ucb_score = model.get_engagement_score(ctx_list)
        interaction.context = {"scores": ctx_list}
        
        db.add(interaction)
        db.commit()

    try:
        if not interaction: # If interaction didn't exist, we still need the model
             model = load_model(learner_id)
             vark = get_latest_vark(learner_id, db)
             if vark:
                ctx_list = vark_to_context(vark["v_score"], vark["a_score"], vark["r_score"], vark["k_score"])
             else:
                ctx_list = [1.0, 0.0, 0.0, 0.0]
             context = np.array(ctx_list)
             action_index = ACTION_TO_INDEX.get(session.instruction_type, 0)
        else:
             # Already calculated context above
             pass

        model.update(action_index, req.reward, context)
        save_model(learner_id, model)
        
        # Optionally update the interaction's ucb_score to reflect the post-update engagement
        if interaction:
             interaction.ucb_score = model.get_engagement_score(ctx_list)
             db.add(interaction)
             db.commit()

    except Exception as e:
        raise HTTPException(500, f"Error processing feedback: {str(e)}")

    # Alerts only after SUCCESS
    # evaluate_alerts(learner_id, db)

    return {
        "status": "model_updated",
        "instruction": session.instruction_type,
        "reward": req.reward
    }
