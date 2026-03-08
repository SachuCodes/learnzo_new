"""
VARK scoring: 20 Yes/No questions. Each question has a modality (V/A/R/K).
Score = count of "yes" per modality. Disability overrides applied.
"""
from typing import Dict, List, Any, Optional
from app.services.vark_questions import VARK_QUESTION_MODALITY


def score_vark_yes_no(responses: List[Dict[str, Any]], disability_type: Optional[str] = None) -> Dict[str, int]:
    """
    responses: list of { "question_id": int, "answer": "yes" | "no" }
    Returns scores for V, A, R, K.
    """
    scores: Dict[str, int] = {"V": 0, "A": 0, "R": 0, "K": 0}

    for r in responses:
        qid = r.get("question_id")
        answer = (r.get("answer") or "").strip().lower()
        modality = VARK_QUESTION_MODALITY.get(qid)
        if modality and answer == "yes":
            scores[modality] = scores.get(modality, 0) + 1

    # Disability-based overrides: disable invalid modalities
    if disability_type:
        d = disability_type.lower()
        if d == "visual" or d == "visual_impairment":
            scores["V"] = -1
            scores["R"] = -1
        elif d == "hearing" or d == "apd":
            scores["A"] = -1
        elif d == "motor" or d == "dyspraxia":
            # Dyspraxia: prefer V, A; don't disable K entirely but instruction_rules override
            pass

    return scores


def get_dominant_style(scores: Dict[str, int]) -> str:
    """Return single dominant modality (V, A, R, K). Tie-break by order V, A, R, K."""
    valid = {k: v for k, v in scores.items() if v >= 0}
    if not valid:
        return "V"
    max_score = max(valid.values())
    for key in ("V", "A", "R", "K"):
        if valid.get(key) == max_score:
            return key
    return "V"


# Legacy: score_vark for old A/B/C/D style (keep for any remaining callers)
def score_vark(responses: List[Dict[str, Any]], disability_type: Optional[str] = None) -> Dict[str, int]:
    """
    Accepts either:
    - New format: [ {"question_id": 1, "answer": "yes"}, ... ]
    - Legacy format: [ {"answer": "V"}, ... ]
    """
    if not responses:
        return {"V": 0, "A": 0, "R": 0, "K": 0}

    first = responses[0]
    if "question_id" in first and "answer" in first:
        return score_vark_yes_no(responses, disability_type)

    # Legacy: direct V/A/R/K answers
    scores = {"V": 0, "A": 0, "R": 0, "K": 0}
    for r in responses:
        ans = (r.get("answer") or "").upper()
        if ans in scores:
            scores[ans] += 1
    if disability_type:
        d = disability_type.lower()
        if d == "visual":
            scores["V"] = -1
            scores["R"] = -1
        elif d == "hearing":
            scores["A"] = -1
        elif d == "motor":
            scores["K"] = -1
    return scores
