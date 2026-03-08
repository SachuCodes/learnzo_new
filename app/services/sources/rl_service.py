from sqlalchemy.orm import Session
from app.models.interaction import Interaction

ALL_STYLES = ["visual", "auditory", "reading", "kinesthetic"]

def get_recommended_style(
    db: Session,
    learner_id: str,
    default_style: str
) -> str:
    """
    Adjusts recommendation based on past rewards.
    Penalizes styles with negative cumulative reward.
    """

    rows = (
        db.query(
            Interaction.recommended_instruction,
            Interaction.reward
        )
        .filter(Interaction.learner_id == learner_id)
        .all()
    )

    if not rows:
        return default_style

    score = {}
    for style, reward in rows:
        score[style] = score.get(style, 0) + reward

    # If default is doing fine, keep it
    if score.get(default_style, 0) >= 0:
        return default_style

    # Otherwise pick best alternative
    candidates = [
        s for s in ALL_STYLES
        if s != default_style
    ]

    # Choose style with highest score (or unexplored)
    return max(
        candidates,
        key=lambda s: score.get(s, 0)
    )
