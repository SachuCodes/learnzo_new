# app/services/logging_service.py

import os
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.learner import Learner
import mysql.connector
from app.db.database import get_db
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LEARNERS_FILE = os.path.join(LOG_DIR, "learners.json")
INTERACTIONS_FILE = os.path.join(LOG_DIR, "interactions.json")


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)


def _save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)





def ensure_learner_exists(learner_id, db):
    learner = db.query(Learner).filter(
        Learner.learner_id == learner_id
    ).first()

    if not learner:
        raise ValueError("Learner does not exist")


def log_interaction(
    learner_id: str,
    context,
    recommended_instruction,
    delivered_instruction,
    reward,
    ucb_score
):
    interactions = _load_json(INTERACTIONS_FILE, [])

    interactions.append({
        "timestamp": datetime.utcnow().isoformat(),
        "learner_id": learner_id,
        "context": context,
        "recommended_instruction": recommended_instruction,
        "delivered_instruction": delivered_instruction,
        "reward": reward,
        "ucb_score": ucb_score
    })

    _save_json(INTERACTIONS_FILE, interactions)

def log_session_summary(
    learner_id: str,
    session_id: str,
    event_type: str,
    data: dict
):
    """
    Log resulting data from quiz or pedagogical feedback.
    Includes current mode and overall engagement score.
    """
    summary_file = os.path.join(LOG_DIR, "session_summaries.json")
    summaries = _load_json(summary_file, [])

    summaries.append({
        "timestamp": datetime.utcnow().isoformat(),
        "learner_id": learner_id,
        "session_id": session_id,
        "event_type": event_type,
        "data": data
    })

    _save_json(summary_file, summaries)

def get_last_interaction(learner_id: str):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT context, recommended_instruction, reward
            FROM interactions
            WHERE learner_id = %s
              AND reward IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (learner_id,)
        )
        row = cursor.fetchone()
        if row:
            row["context"] = json.loads(row["context"])
        return row
    finally:
        cursor.close()
        db.close()
