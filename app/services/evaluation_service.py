# app/services/evaluation_service.py

from collections import defaultdict

# In-memory evaluation (can be persisted later)
ACTION_COUNTS = defaultdict(int)
ACTION_REWARDS = defaultdict(float)

def record_action(action: str, reward: float):
    ACTION_COUNTS[action] += 1
    ACTION_REWARDS[action] += reward

def get_action_stats():
    stats = {}
    for action in ACTION_COUNTS:
        avg_reward = (
            ACTION_REWARDS[action] / ACTION_COUNTS[action]
            if ACTION_COUNTS[action] > 0 else 0
        )
        stats[action] = {
            "count": ACTION_COUNTS[action],
            "average_reward": round(avg_reward, 4)
        }
    return stats
