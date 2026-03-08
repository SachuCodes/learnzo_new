"""
Bandit-based decision: whether to switch learning mode after a session.
Uses quiz score + engagement to decide; LinUCB suggests best mode for next time.
"""
from typing import Optional, Tuple
from sqlalchemy.orm import Session
import numpy as np

from app.models.learner import Learner
from app.models.interaction import Interaction
from app.services.linucb_engine import (
    load_model,
    save_model,
    ACTION_TO_INDEX,
    INDEX_TO_ACTION,
)
from app.services.vark_service import get_latest_vark
from app.services.context_engine import vark_to_context
from app.services.engagement_service import compute_engagement_score

# Thresholds: below these we consider suggesting a mode switch
QUIZ_SCORE_SWITCH_THRESHOLD = 50.0   # percent
ENGAGEMENT_SWITCH_THRESHOLD = 45.0   # overall 0-100


def quiz_score_to_reward(quiz_score: float) -> int:
    """Map 0-100 quiz score to bandit reward -1, 0, 1."""
    if quiz_score >= 70:
        return 1
    if quiz_score >= 40:
        return 0
    return -1


def should_switch_mode(
    learner_id: str,
    current_mode: str,
    quiz_score: float,
    db: Session,
) -> Tuple[bool, Optional[str], str]:
    """
    Decide if we should suggest switching to a different learning mode.
    Uses quiz score and session engagement; LinUCB explores/exploits across modes.
    Returns (should_switch, new_mode or None, reason_string).
    """
    engagement = compute_engagement_score(learner_id, db, lookback_days=30)
    overall_engagement = engagement["overall_score"]

    low_quiz = quiz_score < QUIZ_SCORE_SWITCH_THRESHOLD
    low_engagement = overall_engagement < ENGAGEMENT_SWITCH_THRESHOLD

    if not low_quiz and not low_engagement:
        return False, None, "You're doing well with this learning style."

    try:
        model = load_model(learner_id)
        vark = get_latest_vark(learner_id, db)
        if vark:
            total = (vark["v_score"] or 0) + (vark["a_score"] or 0) + (vark["r_score"] or 0) + (vark["k_score"] or 0)
            if total > 0:
                context = np.array(vark_to_context(
                    vark["v_score"] or 0,
                    vark["a_score"] or 0,
                    vark["r_score"] or 0,
                    vark["k_score"] or 0,
                ))
            else:
                context = np.array([0.25, 0.25, 0.25, 0.25])
        else:
            context = np.array([0.25, 0.25, 0.25, 0.25])

        best_action_index, _ = model.select_action(context)
        bandit_suggested_mode = INDEX_TO_ACTION[best_action_index]

        if bandit_suggested_mode != current_mode:
            reason = "Based on your quiz result and engagement, we're suggesting a different learning style that may work better for you."
            return True, bandit_suggested_mode, reason
    except Exception:
        pass

    return False, None, "We're keeping your current learning style for now."
