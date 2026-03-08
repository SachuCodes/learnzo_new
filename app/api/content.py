from fastapi import APIRouter, HTTPException, Depends
import requests
from gtts import gTTS
import os
import hashlib
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import Content, Learner
from app.auth.dependencies import require_role
from app.services.instruction_rules import INSTRUCTION_RULES
from app.services.instruction_rules import apply_rules
from app.services.rule_engine import resolve_learning_strategy
from app.services.content_generators.visual import generate_visual
from app.services.content_generators.auditory import generate_auditory
from app.services.content_generators.reading import generate_reading
from app.services.content_generators.kinesthetic import generate_kinesthetic
from app.models.session import LearningSession
from app.models.interaction import Interaction
import re
from app.services.strategy_resolver import resolve_instruction_strategy
from app.services.content_safety import is_topic_safe, unsafe_topic_response
from app.services.content_ranking_service import rank_learning_modes, get_recommended_mode
from app.services.quiz_service import generate_quiz_for_topic
from app.services.bandit_decision import (
    quiz_score_to_reward,
    should_switch_mode,
)
from app.services.linucb_engine import load_model, save_model, ACTION_TO_INDEX
from app.services.vark_service import get_latest_vark
from app.services.context_engine import vark_to_context
from pydantic import BaseModel, Field
from typing import List
import numpy as np

router = APIRouter(prefix="/content", tags=["content"])

HEADERS = {
    "User-Agent": "Learnzo-Edu-App/1.0 (contact: demo@learnzo.ai)"
}

AUDIO_DIR = "app/static/audio"

# Ensure audio directory exists
os.makedirs(AUDIO_DIR, exist_ok=True)


# ---------- CONTENT GENERATORS MAP ----------
def get_content_generator(instruction_type: str):
    """Dispatch content generators based on learning style"""
    generators = {
        "reading": generate_reading,
        "visual": generate_visual,
        "auditory": generate_auditory,
        "kinesthetic": generate_kinesthetic
    }
    return generators.get(instruction_type)


@router.get("/adaptive")
def fetch_adaptive_content(
    topic: str,
    user=Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    """
    Generate adaptive content for a topic in all 4 VARK modes.
    Returns all modes with ranking and recommendation.
    """
    learner = db.query(Learner).filter(Learner.user_id == user.id).first()
    if not learner or not learner.learning_style:
        raise HTTPException(status_code=400, detail="Complete VARK assessment first")
    if learner.disability_type is None:
        raise HTTPException(status_code=400, detail="Complete onboarding (disability type) first")
    if not topic or len(topic.strip()) < 3:
        raise HTTPException(status_code=400, detail="Topic must be at least 3 characters")
    if not re.match(r"^[a-zA-Z0-9\s\-']+$", topic.strip()):
        raise HTTPException(status_code=400, detail="Topic contains invalid characters")

    topic_clean = topic.strip()

    # ---------- CHILD SAFETY FILTER ----------
    # Block clearly unsafe / adult topics server-side before any external fetch.
    if not is_topic_safe(topic_clean):
        # Do NOT query external sources; return a safe, explanatory payload.
        # No session or interaction is recorded for blocked topics.
        return {
            "session_id": None,
            "topic": topic_clean,
            "recommended_mode": None,
            "mode_ranking": [],
            "content_by_mode": {},
            "learner_profile": {
                "learning_style": learner.learning_style,
                "disability_type": learner.disability_type,
            },
            **unsafe_topic_response(topic_clean),
        }
    rules = INSTRUCTION_RULES.get(learner.disability_type.strip().lower(), {})
    
    # Rank learning modes based on VARK, disability, and engagement; bandit picks best mode when available
    ranked_modes = rank_learning_modes(learner, db)
    recommended = get_recommended_mode(ranked_modes, learner_id=learner.learner_id, db=db)
    
    # Generate content for all 4 modes
    all_content = {}
    mode_generators = {
        "visual": generate_visual,
        "auditory": generate_auditory,
        "reading": generate_reading,
        "kinesthetic": generate_kinesthetic
    }
    
    for mode, generator in mode_generators.items():
        try:
            content = generator(topic_clean, rules)
            content = apply_rules(content, rules)
            all_content[mode] = content
        except Exception as e:
            # Fallback if generator fails
            all_content[mode] = {
                "type": mode,
                "topic": topic_clean,
                "error": f"Content generation failed: {str(e)}",
                "placeholder": True
            }
    
    # Create session with recommended mode
    session = LearningSession(
        learner_id=learner.learner_id,
        topic=topic_clean,
        learning_style=learner.learning_style,
        disability_type=learner.disability_type,
        instruction_type=recommended["mode"]
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Create Interaction record
    interaction = Interaction(
        learner_id=learner.learner_id,
        session_id=session.id,
        context={
            "learning_style": learner.learning_style,
            "disability_type": learner.disability_type,
            "topic": topic_clean
        },
        recommended_instruction=recommended["mode"],
        delivered_instruction=recommended["mode"]
    )
    db.add(interaction)
    db.commit()

    # Return all modes with ranking
    return {
        "session_id": session.id,
        "topic": topic_clean,
        "recommended_mode": recommended,
        "mode_ranking": [
            {"mode": mode, "score": score, "reason": reason}
            for mode, score, reason in ranked_modes
        ],
        "content_by_mode": all_content,
        "learner_profile": {
            "learning_style": learner.learning_style,
            "disability_type": learner.disability_type
        }
    }





# ---------- TOPIC QUIZ (after content, before "was this helpful" assessment) ------------

@router.get("/quiz")
def get_quiz(
    session_id: str,
    user=Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    """Get topic-based quiz for a learning session. Questions are generated once per session; correct answers stored server-side."""
    learner = db.query(Learner).filter(Learner.user_id == user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    session = (
        db.query(LearningSession)
        .filter(
            LearningSession.id == session_id,
            LearningSession.learner_id == learner.learner_id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session")

    if session.quiz_questions_snapshot:
        return {"session_id": session_id, "questions": session.quiz_questions_snapshot}

    questions_for_client, correct_indices = generate_quiz_for_topic(session.topic, num_questions=10)
    session.quiz_questions_snapshot = questions_for_client
    session.quiz_correct_answers = correct_indices
    db.add(session)
    db.commit()

    return {"session_id": session_id, "questions": questions_for_client}


class QuizAnswerItem(BaseModel):
    question_id: int = Field(..., ge=0)
    selected_index: int = Field(..., ge=0)


class QuizSubmitRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    answers: List[QuizAnswerItem] = Field(..., min_length=1)


@router.post("/quiz/submit")
def submit_quiz(
    payload: QuizSubmitRequest,
    user=Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    """Verify answers, compute score (0-100), store it, update bandit reward, and return whether to switch learning mode."""
    learner = db.query(Learner).filter(Learner.user_id == user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    session = (
        db.query(LearningSession)
        .filter(
            LearningSession.id == payload.session_id,
            LearningSession.learner_id == learner.learner_id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session")

    correct_indices = session.quiz_correct_answers
    if not correct_indices:
        raise HTTPException(status_code=400, detail="No quiz found for this session. Request the quiz first.")

    # Verify and score
    answers_by_id = {a.question_id: a.selected_index for a in payload.answers}
    correct = 0
    for q_index, expected in enumerate(correct_indices):
        if q_index in answers_by_id and answers_by_id[q_index] == expected:
            correct += 1
    score = (correct / len(correct_indices)) * 100.0 if correct_indices else 0.0

    session.quiz_score = round(score, 2)
    db.add(session)

    # Update interaction reward for this session (for engagement/bandit)
    interaction = (
        db.query(Interaction)
        .filter(Interaction.session_id == payload.session_id)
        .first()
    )
    reward = quiz_score_to_reward(score)
    if interaction:
        interaction.reward = reward
        interaction.delivered_instruction = session.instruction_type
        db.add(interaction)
    db.commit()

    # Update LinUCB with this reward so bandit explores/exploits modes
    try:
        model = load_model(learner.learner_id)
        vark = get_latest_vark(learner.learner_id, db)
        if vark:
            total = (vark["v_score"] or 0) + (vark["a_score"] or 0) + (vark["r_score"] or 0) + (vark["k_score"] or 0)
            context = np.array(vark_to_context(
                vark["v_score"] or 0,
                vark["a_score"] or 0,
                vark["r_score"] or 0,
                vark["k_score"] or 0,
            )) if total > 0 else np.array([0.25, 0.25, 0.25, 0.25])
        else:
            context = np.array([0.25, 0.25, 0.25, 0.25])
        action_index = ACTION_TO_INDEX.get(session.instruction_type, 0)
        model.update(action_index, float(reward), context)
        save_model(learner.learner_id, model)
    except Exception:
        pass

    # Decide if we should suggest switching learning mode
    switch, new_mode, reason = should_switch_mode(
        learner.learner_id,
        session.instruction_type or "visual",
        score,
        db,
    )

    return {
        "score": round(score, 2),
        "correct": correct,
        "total": len(correct_indices),
        "switch_mode": switch,
        "new_mode": new_mode,
        "reason": reason,
    }


# ---------- RECOMMENDED CONTENT ----------------

@router.get("/recommended")
def get_recommended_content(
    user=Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    learner = db.query(Learner).filter(
        Learner.user_id == user.id
    ).first()

    if not learner or not learner.learning_style:
        raise HTTPException(status_code=400, detail="Complete VARK assessment first")

    content = db.query(Content).filter(
        Content.learning_style == learner.learning_style
    ).all()

    if not content:
        return {"message": "No recommended content available yet"}

    return content