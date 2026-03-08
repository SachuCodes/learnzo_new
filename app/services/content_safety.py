"""
Content safety utilities for child-only Learnzo deployment.

Rules:
- Platform is strictly for under-18 learners.
- Adult / unsafe topics must never be served, even via search.
- Filtering is enforced server-side before any external content fetch.
"""

from typing import Tuple


# Minimal keyword-based safety net.
# In a production system this should be replaced or augmented
# with a dedicated content safety service / classifier.
UNSAFE_KEYWORDS = {
    "sex",
    "porn",
    "pornography",
    "nude",
    "nudity",
    "fetish",
    "violence",
    "violent",
    "murder",
    "kill",
    "suicide",
    "self-harm",
    "drugs",
    "alcohol",
    "gambling",
    "weapon",
    "gun",
    "terror",
    "extremism",
}


def is_topic_safe(raw_topic: str) -> bool:
    """
    Very conservative topic safety check.
    Returns False if the topic clearly contains unsafe keywords.
    """
    topic = (raw_topic or "").lower()
    # Simple word-based check; split on spaces and punctuation.
    tokens = {t.strip(" .,!?:;\"'") for t in topic.split()}
    for kw in UNSAFE_KEYWORDS:
        if kw in tokens or kw in topic:
            return False
    return True


def unsafe_topic_response(topic: str) -> dict:
    """
    Child-friendly fallback payload for blocked topics.
    Returned instead of normal learning content.
    """
    clean_topic = (topic or "").strip()
    return {
        "blocked": True,
        "message": (
            "This topic is not appropriate for Learnzo's age group. "
            "Please choose a different topic to learn about."
        ),
        "topic": clean_topic,
    }

