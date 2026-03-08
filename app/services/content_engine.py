# app/services/content_engine.py

STATIC_CONTENT = {
    ("Photosynthesis", "visual", "easy"): {
        "type": "visual",
        "description": "Simple diagram showing how plants use sunlight, water, and CO2 to make food."
    },

    ("Photosynthesis", "auditory", "easy"): {
        "type": "audio",
        "script": "Photosynthesis is how plants make their own food using sunlight, water, and air."
    },

    ("Photosynthesis", "text", "easy"): {
        "type": "text",
        "content": "Photosynthesis is the process by which plants prepare food using sunlight."
    },

    ("Photosynthesis", "visual", "medium"): {
        "type": "visual",
        "description": "Labeled diagram showing light reactions and Calvin cycle."
    },

    ("Photosynthesis", "auditory", "medium"): {
        "type": "audio",
        "script": "Photosynthesis occurs in chloroplasts and involves light-dependent and light-independent reactions."
    },

    ("Photosynthesis", "text", "medium"): {
        "type": "text",
        "content": "Photosynthesis consists of light-dependent reactions and the Calvin cycle."
    }
}


def generate_content(modality: str, topic: str, difficulty: str = "easy"):
    """
    Static content retrieval.
    Priority: exact match → fallback by modality → generic fallback
    """

    # Exact match
    key = (topic, modality, difficulty)
    if key in STATIC_CONTENT:
        return STATIC_CONTENT[key]

    # Fallback: any content with same topic + modality
    for (t, m, d), content in STATIC_CONTENT.items():
        if t == topic and m == modality:
            return content

    # Final fallback
    return {
        "type": "text",
        "content": f"Basic explanation of {topic}."
    }
