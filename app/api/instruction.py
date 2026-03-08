# app/api/instruction.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session as Session
from pydantic import BaseModel
import json
from app.db.database import get_db
from app.services.linucb_engine import load_model, save_model, INDEX_TO_ACTION
from app.services.logging_service import ensure_learner_exists
from app.services.vark_service import get_latest_vark
from app.services.context_engine import vark_to_context
from app.models.interaction import Interaction
from app.auth.dependencies import require_role, get_current_user   
from sqlalchemy.orm import Session as DBSession
from app.models.session import LearningSession

router = APIRouter(prefix="/instruction", tags=["instruction"])


class InstructionRequest(BaseModel):
    pass



@router.post("/next")
def next_instruction(
    user=Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    learner_id = user.learner.learner_id

    ensure_learner_exists(learner_id, db)

    vark = get_latest_vark(learner_id, db)
    if not vark:
        raise HTTPException(status_code=400, detail="VARK not completed")

    context = vark_to_context(
        v=vark["v_score"],
        a=vark["a_score"],
        r=vark["r_score"],
        k=vark["k_score"],
    )

    model = load_model(learner_id)

    learning_session = LearningSession(
        learner_id=learner_id,
        topic="default"
    )
    db.add(learning_session)
    db.commit()
    db.refresh(learning_session)

    action_index, ucb_score = model.select_action(context)
    instruction = INDEX_TO_ACTION[action_index]

    learning_session.instruction_type = instruction
    learning_session.learning_style = instruction[0].upper()

    interaction = Interaction(
        learner_id=learner_id,
        session_id=learning_session.id,
        context=json.dumps(context),
        recommended_instruction=instruction,
        delivered_instruction=instruction,
        ucb_score=float(ucb_score)
    )

    db.add(interaction)
    db.commit()

    save_model(learner_id, model)

    return {
        "session_id": learning_session.id,
        "instruction_type": instruction,
        "learning_style": learning_session.learning_style,
        "context_used": context,
        "ucb_score": round(float(ucb_score), 4)
    }
