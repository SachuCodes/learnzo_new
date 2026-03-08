"""Visual content generator. Uses Gemini AI for visual learning guides and YouTube search."""
from app.services.ai_service import generate_text

def generate_visual(topic: str, rules: dict):
    """
    Generate visual learning guidance for a topic using Gemini.
    """
    tone = rules.get("tone", "friendly and educational")
    
    prompt = f"""
    You are an expert educator. Create a 'Visual Learning Guide' for the topic: "{topic}".
    
    Target Student Profile:
    - Tone: {tone}
    - Describe the topic using vivid, visual language.
    - Provide 3-4 'Mental Imagery' exercises where the student imagines specific visual aspects of {topic}.
    - Format as a descriptive guide.
    
    Output only the visual guide text.
    """
    
    instruction = generate_text(prompt)

    if not instruction:
        instruction = f"Observe and imagine the different parts of {topic}. Visualize how it looks, its colors, and its shapes."

    return {
        "type": "visual",
        "topic": topic,
        "instruction": instruction,
        "images": [], # No longer scraping unreliable Wikimedia images
        "youtube_search_url": f"https://www.youtube.com/results?search_query={topic}",
        "rules_applied": rules,
        "source": "gemini-ai"
    }
