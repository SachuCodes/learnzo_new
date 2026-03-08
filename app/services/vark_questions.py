"""
VARK questionnaire: 20 Yes/No questions.
Distribution: 5 Visual, 5 Auditory, 5 Reading/Writing, 5 Kinesthetic.
Simple language for children.
"""
from typing import List, Dict, Any, Optional

# question_id -> modality (V, A, R, K). 5 per modality.
VARK_QUESTION_MODALITY: Dict[int, str] = {
    1: "V", 2: "V", 3: "V", 4: "V", 5: "V",
    6: "A", 7: "A", 8: "A", 9: "A", 10: "A",
    11: "R", 12: "R", 13: "R", 14: "R", 15: "R",
    16: "K", 17: "K", 18: "K", 19: "K", 20: "K",
}

# Child-friendly question text (short, clear)
VARK_QUESTION_TEXTS: Dict[int, str] = {
    1: "I like to learn with pictures and videos.",
    2: "I remember things better when I see them.",
    3: "I like charts and diagrams.",
    4: "I like to watch someone show me how.",
    5: "I like colorful notes and drawings.",
    6: "I like to learn by listening.",
    7: "I remember what I hear.",
    8: "I like when someone explains out loud.",
    9: "I like songs and rhymes to learn.",
    10: "I like to talk about what I learn.",
    11: "I like to read and write to learn.",
    12: "I like lists and written steps.",
    13: "I like to take notes.",
    14: "I like to read books and handouts.",
    15: "I like to write things down to remember.",
    16: "I like to do things with my hands.",
    17: "I like to try it myself.",
    18: "I like moving while I learn.",
    19: "I like building or making things.",
    20: "I like activities and games.",
}


def get_vark_questions_list() -> List[Dict[str, Any]]:
    """Return list of { question_id, text, modality } for API."""
    return [
        {
            "question_id": qid,
            "text": VARK_QUESTION_TEXTS[qid],
            "modality": VARK_QUESTION_MODALITY[qid],
        }
        for qid in sorted(VARK_QUESTION_MODALITY.keys())
    ]


def get_question_modality(question_id: int) -> Optional[str]:
    return VARK_QUESTION_MODALITY.get(question_id)
