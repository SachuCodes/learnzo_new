"""
AI-based dynamic quiz generation for learning sessions using Google Gemini.
Generates content-dependent questions based on the topic.
"""
import random
import logging
from typing import List, Dict, Any, Tuple
from app.services.ai_service import generate_json

logger = logging.getLogger("learnzo")

# Fallback templates in case AI fails
QUIZ_TEMPLATES: List[Dict[str, Any]] = [
    {
        "text": "What is the primary focus when studying {topic}?",
        "options": ["Understanding core concepts", "Memorizing dates only", "Ignoring the details", "Looking at unrelated topics"],
        "correct_index": 0,
    },
    {
        "text": "Which of these is a common characteristic of {topic}?",
        "options": ["It has specific principles", "It is completely random", "It never changes", "It has no practical use"],
        "correct_index": 0,
    },
    {
        "text": "Why is it important to have a good grasp of {topic}?",
        "options": ["It provides a foundation for further learning", "It is a requirement for graduation only", "It helps in winning games", "It is not important at all"],
        "correct_index": 0,
    },
    {
        "text": "In the context of {topic}, what does success typically look like?",
        "options": ["Applying knowledge effectively", "Finishing the book quickly", "Asking no questions", "Repeating what others say"],
        "correct_index": 0,
    },
]

def generate_quiz_for_topic(topic: str, num_questions: int = 10) -> Tuple[List[Dict[str, Any]], List[int]]:
    """
    Generate quiz questions for a topic using Gemini.
    """
    prompt = f"""
    Generate a high-quality educational quiz for a student learning about: "{topic}".
    
    Requirements:
    - Generate exactly {num_questions} multiple-choice questions.
    - Each question must be highly relevant to "{topic}".
    - Each question must have exactly 4 options.
    - Provide the output in strictly valid JSON format.
    - The JSON should be a list of objects, each with:
      - "text": The question text.
      - "options": A list of 4 strings.
      - "correct_index": The 0-based index of the correct option.
    
    Example:
    [
      {{
        "text": "Question about {topic}?",
        "options": ["Wrong", "Correct", "Wrong", "Wrong"],
        "correct_index": 1
      }}
    ]
    """
    
    questions_data = generate_json(prompt)
    
    if questions_data and isinstance(questions_data, list):
        correct_indices = []
        questions_for_client = []
        
        for idx, q in enumerate(questions_data):
            if idx >= num_questions: break
            if all(k in q for k in ["text", "options", "correct_index"]):
                correct_indices.append(q["correct_index"])
                questions_for_client.append({
                    "id": idx,
                    "text": q["text"],
                    "options": q["options"]
                })
        
        if len(questions_for_client) >= 1:
            return questions_for_client, correct_indices

    # Fallback to static templates
    return _generate_fallback_quiz(topic, num_questions)


def _generate_fallback_quiz(topic: str, num_questions: int) -> Tuple[List[Dict[str, Any]], List[int]]:
    topic_display = topic.title()
    pool = []
    for i, t in enumerate(QUIZ_TEMPLATES):
        text = t["text"].format(topic=topic_display)
        options = list(t["options"])
        correct_index = t["correct_index"]
        pool.append((i, text, options, correct_index))

    # If we need more than we have in pool, we repeat some with slight variations or just cap it
    selected = []
    if num_questions <= len(pool):
        selected = random.sample(pool, num_questions)
    else:
        selected = pool + random.choices(pool, k=num_questions - len(pool))

    correct_indices = []
    questions_for_client = []

    for idx, (_, text, options, correct_index) in enumerate(selected):
        correct_indices.append(correct_index)
        questions_for_client.append({
            "id": idx,
            "text": text,
            "options": options,
        })

    return questions_for_client, correct_indices
