import numpy as np
import os
import pickle
import random

# ================= CONFIG =================
ACTIONS = ["visual", "auditory", "reading", "kinesthetic"]
ACTION_TO_INDEX = {a: i for i, a in enumerate(ACTIONS)}
INDEX_TO_ACTION = {i: a for a, i in ACTION_TO_INDEX.items()}

CONTEXT_DIM = 4
ALPHA = 0.5

MODEL_DIR = "linucb_states"
os.makedirs(MODEL_DIR, exist_ok=True)

DEBUG = True  # set False in production
# ==========================================


class LinUCB:
    """
    Linear Upper Confidence Bound (LinUCB) contextual bandit.
    Each action maintains its own linear reward model.
    """

    def __init__(self, n_actions: int, d: int, alpha: float = 0.5):
        self.n_actions = n_actions
        self.d = d
        self.alpha = alpha

        # One covariance matrix and reward vector per action
        self.A = [np.identity(d) for _ in range(n_actions)]
        self.b = [np.zeros(d) for _ in range(n_actions)]

    def select_action(self, context):
        """
        Selects the best action using UCB score.
        """
        context = np.array(context)
        if len(context) != self.d:
             # Handle dimension mismatch (e.g. if context was passed as list/None)
             context = np.zeros(self.d)
             context[0] = 1.0 # Default fallback
    
        if random.random() < 0.1:  # 10% forced exploration
          return random.randint(0, self.n_actions - 1), 0.0

        scores = []

        for a in range(self.n_actions):
            try:
                A_inv = np.linalg.inv(self.A[a])
            except np.linalg.LinAlgError:
                # Fallback for singular matrix
                A_inv = np.identity(self.d)
            
            theta = A_inv @ self.b[a]

            mean = float(theta @ context)
            uncertainty = float(self.alpha * np.sqrt(max(0, context @ A_inv @ context)))
            score = mean + uncertainty
            scores.append(score)

            if DEBUG:
                print(f"Action: {INDEX_TO_ACTION[a]}")
                print(f"  Mean reward: {mean:.4f}")
                print(f"  Uncertainty: {uncertainty:.4f}")
                print(f"  Total score: {score:.4f}")

        best_action = int(np.argmax(scores))
        best_score = float(scores[best_action])
        
        if DEBUG:
            print(f"Selected action index: {best_action}")

        return best_action, best_score

    def update(self, action: int, reward: float, context):
        """
        Updates model parameters after observing reward.
        """
        context = np.array(context)
        assert len(context) == self.d, "Context dimension mismatch"

        self.A[action] += np.outer(context, context)
        self.b[action] += reward * context

    def get_engagement_score(self, context):
        """
        Computes an overall engagement score based on current model parameters
        for the given context. It averages the estimated mean rewards across actions.
        """
        context = np.array(context)
        if len(context) != self.d:
            context = np.zeros(self.d)
            context[0] = 1.0

        total_mean_reward = 0.0
        for a in range(self.n_actions):
            try:
                A_inv = np.linalg.inv(self.A[a])
            except np.linalg.LinAlgError:
                A_inv = np.identity(self.d)
            
            theta = A_inv @ self.b[a]
            mean = float(theta @ context)
            total_mean_reward += mean

        # Average mean reward across all possible instructional actions
        avg_engagement = total_mean_reward / self.n_actions
        return avg_engagement

    def get_action_scores(self, context):
        """
        Returns the mean reward (engagement) for each action individually.
        """
        context = np.array(context)
        if len(context) != self.d:
            context = np.zeros(self.d)
            context[0] = 1.0

        action_scores = {}
        for a in range(self.n_actions):
            try:
                A_inv = np.linalg.inv(self.A[a])
            except np.linalg.LinAlgError:
                A_inv = np.identity(self.d)
            
            theta = A_inv @ self.b[a]
            mean = float(theta @ context)
            action_scores[INDEX_TO_ACTION[a]] = mean
        
        return action_scores


# =============== PERSISTENCE ===============

def _model_path(learner_id: str) -> str:
    return os.path.join(MODEL_DIR, f"{learner_id}.pkl")


def load_model(learner_id: str) -> LinUCB:
    """
    Loads an existing learner model or creates a new one.
    """
    path = _model_path(learner_id)

    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)

    return LinUCB(
        n_actions=len(ACTIONS),
        d=CONTEXT_DIM,
        alpha=ALPHA
    )


def save_model(learner_id: str, model: LinUCB):
    """
    Persists learner model to disk.
    """
    with open(_model_path(learner_id), "wb") as f:
        pickle.dump(model, f)
# ==========================================

def get_engagement_description(score, previous_score=None):
    """
    Translates numeric engagement score and trend into words.
    """
    # Score interpretation
    if score > 0.6:
        desc = "Excellent"
    elif score > 0.2:
        desc = "Good"
    elif score > -0.2:
        desc = "Steady"
    elif score > -0.6:
        desc = "Declining"
    else:
        desc = "Needs Intervention"

    # Trend interpretation (if previous score is available)
    if previous_score is not None:
        change = score - previous_score
        if change > 0.1:
            desc += " and Improving"
        elif change < -0.1:
            desc += " but Decreasing"
        else:
            desc += " and Stable"
    
    return desc
