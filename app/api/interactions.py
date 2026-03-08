# app/api/interactions.py

from fastapi import APIRouter, HTTPException, Depends
import json
import numpy as np

from app.auth.dependencies import require_role, get_current_user
from app.db.database import get_db
from app.services.linucb_engine import load_model, INDEX_TO_ACTION
from app.services.content_service import fetch_content
from app.services.logging_service import ensure_learner_exists

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post("/start", dependencies=[Depends(require_role("student"))])
def start_interaction(topic: str, user=Depends(get_current_user)):
    learner_id = user["learner_id"]

    if not learner_id:
        raise HTTPException(400, "Learner not linked to account")

    ensure_learner_exists(learner_id)

    # 1️⃣ Build context (simple version)
    context = np.array([1.0, 0.0, 0.0, 0.0])  # later → dynamic
    context_json = json.dumps(context.tolist())

    # 2️⃣ Load model & choose action
    model = load_model(learner_id)
    action_index, ucb_score = model.select_action(context)
    instruction = INDEX_TO_ACTION[action_index]

    # 3️⃣ Fetch real content
    content = fetch_content(instruction, topic)

    # 4️⃣ Log interaction
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO interactions
        (learner_id, topic, context, recommended_instruction,
         delivered_instruction, ucb_score)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            learner_id,
            topic,
            context_json,
            instruction,
            instruction,
            float(ucb_score)
        )
    )

    db.commit()
    cursor.close()
    db.close()

    return {
        "learner_id": learner_id,
        "topic": topic,
        "instruction": instruction,
        "ucb_score": round(float(ucb_score), 4),
        "content": content
    }
