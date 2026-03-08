# app/services/alert_engine.py

from sqlalchemy.orm import Session

NEGATIVE_STREAK = 3
LOW_ENGAGEMENT_THRESHOLD = -0.3


def evaluate_alerts(learner_id, db):
    # TODO: rewrite using SQLAlchemy ORM
    return



def create_alert(learner_id, modality, alert_type, severity, message, db: Session = None):
    """
    Create an alert for a learner.
    This is a placeholder since alerts table hasn't been fully integrated yet.
    """
    if db is None:
        return
    
    # TODO: Implement alert creation once alerts table is properly integrated
    # For now, this is a no-op
    pass
