"""
Content Ranking Service

Ranks learning modes (V/A/R/K) based on:
- Initial VARK assessment results
- Disability type constraints
- Ongoing engagement data (which modes get positive feedback)

Architecture: Clean service layer, data-driven ranking.
"""
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.learner import Learner
from app.models.vark_response import VARKResponse
from app.models.interaction import Interaction
from app.services.instruction_rules import INSTRUCTION_RULES


def rank_learning_modes(
    learner: Learner,
    db: Session,
    lookback_days: int = 30
) -> List[Tuple[str, float, str]]:
    """
    Rank learning modes for a learner.
    
    Returns:
        List of (mode, score, reason) tuples, sorted by score descending.
        Modes: "visual", "auditory", "reading", "kinesthetic"
        Score: 0-100
        Reason: Human-readable explanation
    """
    from datetime import datetime, timedelta
    
    # Base scores from VARK assessment
    vark_scores = {"V": 0, "A": 0, "R": 0, "K": 0}
    latest_vark = (
        db.query(VARKResponse)
        .filter(VARKResponse.learner_id == learner.learner_id)
        .order_by(VARKResponse.created_at.desc())
        .first()
    )
    
    if latest_vark:
        vark_scores = {
            "V": latest_vark.v_score or 0,
            "A": latest_vark.a_score or 0,
            "R": latest_vark.r_score or 0,
            "K": latest_vark.k_score or 0
        }
    
    # Map VARK to instruction types
    mode_map = {
        "V": "visual",
        "A": "auditory",
        "R": "reading",
        "K": "kinesthetic"
    }
    
    # Start with VARK scores normalized to 0-100
    base_scores = {}
    max_vark = max(vark_scores.values()) if vark_scores.values() else 1
    for vark_key, mode in mode_map.items():
        if max_vark > 0:
            base_scores[mode] = (vark_scores[vark_key] / max_vark) * 100
        else:
            base_scores[mode] = 25.0  # Equal if no VARK data
    
    # Apply disability constraints
    if learner.disability_type:
        rules = INSTRUCTION_RULES.get(learner.disability_type.lower(), {})
        preferred = rules.get("preferred_styles", [])
        
        # Boost preferred styles
        for pref in preferred:
            mode = mode_map.get(pref)
            if mode:
                base_scores[mode] = min(100, base_scores[mode] * 1.3)
        
        # Penalize disabled styles
        if learner.disability_type.lower() in ["visual", "visual_impairment"]:
            base_scores["visual"] *= 0.1
            base_scores["reading"] *= 0.1
        elif learner.disability_type.lower() in ["hearing", "apd"]:
            base_scores["auditory"] *= 0.1
    
    # Adjust based on engagement data (which modes get positive feedback)
    cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
    interactions = (
        db.query(Interaction)
        .filter(
            and_(
                Interaction.learner_id == learner.learner_id,
                Interaction.created_at >= cutoff_date,
                Interaction.reward.isnot(None)
            )
        )
        .all()
    )
    
    engagement_by_mode = {"visual": [], "auditory": [], "reading": [], "kinesthetic": []}
    for interaction in interactions:
        mode = interaction.delivered_instruction
        if mode in engagement_by_mode and interaction.reward is not None:
            engagement_by_mode[mode].append(interaction.reward)
    
    # Calculate average reward per mode and adjust scores
    for mode, rewards in engagement_by_mode.items():
        if rewards:
            avg_reward = sum(rewards) / len(rewards)
            # Positive reward boosts, negative penalizes
            adjustment = avg_reward * 10  # Scale -1 to 1 into -10 to +10
            base_scores[mode] = max(0, min(100, base_scores[mode] + adjustment))
    
    # Generate reasons
    reasons = {}
    dominant_vark = max(vark_scores, key=vark_scores.get) if vark_scores else None
    if dominant_vark:
        reasons[mode_map[dominant_vark]] = f"Based on VARK assessment ({dominant_vark} dominant)"
    
    if learner.disability_type:
        reasons["visual"] = reasons.get("visual", "") + f" | Disability: {learner.disability_type}"
    
    # Sort by score
    ranked = sorted(
        [(mode, base_scores[mode], reasons.get(mode, "Based on assessment")) for mode in mode_map.values()],
        key=lambda x: x[1],
        reverse=True
    )
    
    return ranked


def get_recommended_mode(
    ranked_modes: List[Tuple[str, float, str]],
    learner_id: str | None = None,
    db: Session | None = None,
) -> Dict[str, any]:
    """
    Extract the recommended mode. If learner_id and db are provided and we have
    a bandit model, use LinUCB suggestion to explore/exploit learning modes.
    """
    if not ranked_modes:
        return {"mode": "visual", "score": 50.0, "reason": "Default recommendation"}

    fallback_mode, fallback_score, fallback_reason = ranked_modes[0]
    fallback = {
        "mode": fallback_mode,
        "score": round(fallback_score, 2),
        "reason": fallback_reason,
    }

    if learner_id and db:
        try:
            from app.services.linucb_engine import load_model, INDEX_TO_ACTION
            from app.services.vark_service import get_latest_vark
            from app.services.context_engine import vark_to_context
            import numpy as np

            model = load_model(learner_id)
            vark = get_latest_vark(learner_id, db)
            if vark:
                total = (vark.get("v_score") or 0) + (vark.get("a_score") or 0) + (vark.get("r_score") or 0) + (vark.get("k_score") or 0)
                context = np.array(
                    vark_to_context(
                        vark.get("v_score") or 0,
                        vark.get("a_score") or 0,
                        vark.get("r_score") or 0,
                        vark.get("k_score") or 0,
                    )
                ) if total > 0 else np.array([0.25, 0.25, 0.25, 0.25])
            else:
                context = np.array([0.25, 0.25, 0.25, 0.25])
            best_index, _ = model.select_action(context)
            bandit_mode = INDEX_TO_ACTION[best_index]
            # Use bandit suggestion; keep score/reason from ranking for that mode if present
            for mode, score, reason in ranked_modes:
                if mode == bandit_mode:
                    return {"mode": mode, "score": round(score, 2), "reason": f"Best fit for you (bandit): {reason}"}
            return {"mode": bandit_mode, "score": round(fallback_score, 2), "reason": "Best fit for you (bandit)"}
        except Exception:
            pass

    return fallback
