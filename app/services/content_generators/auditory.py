"""Auditory content generator. Provides text optimized for TTS using Gemini AI."""
from app.services.ai_service import generate_text

def generate_auditory(topic: str, rules: dict):
    """
    Generate auditory content for a topic using Gemini.
    Returns text optimized for Read-Aloud.
    """
    tone = rules.get("tone", "friendly and educational")
    
    prompt = f"""
    You are an expert educator. Generate a high-quality educational text about "{topic}" 
    that is specifically written to be READ ALOUD.
    
    Target Student Profile:
    - Tone: {tone}
    - Use clear, descriptive language.
    - Keep sentences relatively short for easy listening.
    - Avoid complex formatting or lists; focus on natural-sounding narrative.
    
    Output only the educational text itself.
    """
    
    text = generate_text(prompt)

    if not text:
        text = (
            f"Let's learn about {topic}. Listen carefully to this information. "
            f"Hearing facts explained clearly helps you understand and remember new things. "
            f"Take a moment to think about what you've heard."
        )

    return {
        "type": "auditory",
        "text": text,
        "source": "gemini-ai",
    }
