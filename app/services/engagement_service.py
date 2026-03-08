"""
Engagement Score Calculation Service

Computes normalized engagement scores (0-100%) based on:
- Learning session duration (normalized by expected duration)
- Interaction frequency (sessions per week)
- Completed activities (sessions with positive feedback)
- Feedback quality (reward scores, engagement ratings)

Architecture: Clean service layer, no hardcoded thresholds.
"""
from typing import Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.session import LearningSession
from app.models.interaction import Interaction
from app.models.learning_feedback import LearningFeedback


EXPECTED_SESSION_DURATION_MINUTES = 15
EXPECTED_SESSIONS_PER_WEEK = 3


def compute_engagement_score(learner_id: str, db: Session, lookback_days: int = 30) -> Dict[str, float]:
    cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
    sessions = (
        db.query(LearningSession)
        .filter(and_(LearningSession.learner_id == learner_id, LearningSession.created_at >= cutoff_date))
        .all()
    )
    if not sessions:
        return {
            "overall_score": 0.0,
            "session_duration_score": 0.0,
            "interaction_frequency_score": 0.0,
            "completion_score": 0.0,
            "feedback_score": 0.0,
            "breakdown": {"total_sessions": 0, "avg_duration_minutes": 0.0, "sessions_per_week": 0.0, "completion_rate": 0.0, "avg_reward": 0.0, "avg_engagement_rating": 0.0}
        }
    session_durations = []
    for session in sessions:
        interactions = db.query(Interaction).filter(Interaction.session_id == session.id).order_by(Interaction.created_at).all()
        if interactions and len(interactions) > 1:
            duration = (interactions[-1].created_at - interactions[0].created_at).total_seconds() / 60
            session_durations.append(max(duration, 1.0))
        else:
            session_durations.append(EXPECTED_SESSION_DURATION_MINUTES * 0.5)
    avg_duration = sum(session_durations) / len(session_durations) if session_durations else 0
    duration_score = min(100, (avg_duration / EXPECTED_SESSION_DURATION_MINUTES) * 100)
    days_span = max(1, (datetime.utcnow() - cutoff_date).days)
    sessions_per_week = (len(sessions) / days_span) * 7
    frequency_score = min(100, (sessions_per_week / EXPECTED_SESSIONS_PER_WEEK) * 100)
    session_ids = [s.id for s in sessions]
    interactions_with_reward = db.query(Interaction).filter(and_(Interaction.session_id.in_(session_ids), Interaction.reward.isnot(None))).all()
    positive_feedback_count = sum(1 for i in interactions_with_reward if i.reward and i.reward > 0)
    completion_rate = (positive_feedback_count / len(sessions)) * 100 if sessions else 0
    completion_score = min(100, completion_rate)
    avg_reward = 0.0
    if interactions_with_reward:
        rewards = [i.reward for i in interactions_with_reward if i.reward is not None]
        avg_reward = sum(rewards) / len(rewards) if rewards else 0
        feedback_score_from_reward = ((avg_reward + 1) / 2) * 100
    else:
        feedback_score_from_reward = 0
    feedbacks = db.query(LearningFeedback).filter(LearningFeedback.session_id.in_(session_ids)).all()
    avg_engagement_rating = 0.0
    if feedbacks:
        ratings = [f.engagement for f in feedbacks if f.engagement]
        avg_engagement_rating = sum(ratings) / len(ratings) if ratings else 0
        feedback_score_from_rating = ((avg_engagement_rating - 1) / 4) * 100
    else:
        feedback_score_from_rating = 0
    feedback_score = (feedback_score_from_reward * 0.6 + feedback_score_from_rating * 0.4)
    overall_score = (duration_score * 0.25 + frequency_score * 0.25 + completion_score * 0.25 + feedback_score * 0.25)
    return {
        "overall_score": round(overall_score, 2),
        "session_duration_score": round(duration_score, 2),
        "interaction_frequency_score": round(frequency_score, 2),
        "completion_score": round(completion_score, 2),
        "feedback_score": round(feedback_score, 2),
        "breakdown": {
            "total_sessions": len(sessions),
            "avg_duration_minutes": round(avg_duration, 2),
            "sessions_per_week": round(sessions_per_week, 2),
            "completion_rate": round(completion_rate, 2),
            "avg_reward": round(avg_reward, 2),
            "avg_engagement_rating": round(avg_engagement_rating, 2)
        }
    }


def get_aggregate_engagement_for_teacher(
    db: Session, lookback_days: int = 30, learner_ids: list[str] | None = None
) -> Dict[str, any]:
    """
    Get aggregate engagement. If learner_ids is None, include all learners (backward compat).
    """
    from app.models.learner import Learner
    q = db.query(Learner).filter(Learner.name.isnot(None))
    if learner_ids is not None:
        q = q.filter(Learner.learner_id.in_(learner_ids))
    learners = q.all()
    if not learners:
        return {"total_students": 0, "engagement_distribution": {"high": 0, "medium": 0, "low": 0}, "avg_engagement": 0.0, "students": []}
    student_scores = []
    for learner in learners:
        score_data = compute_engagement_score(learner.learner_id, db, lookback_days)
        student_scores.append({"learner_id": learner.learner_id, "name": learner.name or "Unknown", "score": score_data["overall_score"]})
    high = sum(1 for s in student_scores if s["score"] >= 70)
    medium = sum(1 for s in student_scores if 40 <= s["score"] < 70)
    low = sum(1 for s in student_scores if s["score"] < 40)
    avg_engagement = sum(s["score"] for s in student_scores) / len(student_scores) if student_scores else 0
    return {
        "total_students": len(learners),
        "engagement_distribution": {"high": high, "medium": medium, "low": low},
        "avg_engagement": round(avg_engagement, 2),
        "students": student_scores
    }
