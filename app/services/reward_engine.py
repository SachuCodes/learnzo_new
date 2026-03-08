# app/services/reward_engine.py

from app.core.config import (
    ENGAGEMENT_INCREASE_REWARD,
    TASK_COMPLETION_REWARD,
    DROPOUT_PENALTY
)

def compute_reward(feedback):
    reward = 0.0

    if feedback.engagement_delta > 0:
        reward += ENGAGEMENT_INCREASE_REWARD

    if feedback.task_completed:
        reward += TASK_COMPLETION_REWARD

    if feedback.time_spent < feedback.expected_time:
        reward += 0.5

    if getattr(feedback, "dropped_out", False):
        reward += DROPOUT_PENALTY

    return reward
