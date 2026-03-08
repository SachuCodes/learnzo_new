"""Reading/Writing content generator. Uses Gemini AI for educational text."""
from app.services.ai_service import generate_text

def generate_reading(topic: str, rules: dict):
    """
    Generate reading/writing content for a topic using Gemini.
    """
    tone = rules.get("tone", "friendly and educational")
    max_chars = rules.get("max_content_length", 1500)
    
    prompt = f"""
    You are an expert educator. Generate a high-quality educational reading text about "{topic}".
    
    Target Student Profile:
    - Tone: {tone}
    - Maximum length: {max_chars} characters.
    - Simplified vocabulary and clear structure.
    
    The content should be engaging, factually accurate, and suitable for a student to read and take notes from.
    Output only the educational text itself.
    """
    
    text = generate_text(prompt)
    
    if not text:
        text = (
            f"Here is some information about {topic}. "
            f"Learning about this topic involves understanding its core principles and history. "
            f"You can take notes or write a summary to help you remember what you've learned."
        )

    return {
        "type": "reading",
        "title": topic.title(),
        "text": text,
        "source": "gemini-ai",
    }
