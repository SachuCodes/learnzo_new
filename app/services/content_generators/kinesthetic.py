"""Kinesthetic content generator. Generates hands-on activities using Gemini AI."""
from app.services.ai_service import generate_json

def generate_kinesthetic(topic: str, rules: dict):
    """
    Generate kinesthetic (hands-on) activities for a topic using Gemini.
    """
    tone = rules.get("tone", "energetic and hands-on")
    
    prompt = f"""
    You are an expert educator. Generate 5 hands-on, physical activities for a student 
    learning about "{topic}".
    
    Target Student Profile:
    - Tone: {tone}
    - Activities should be safe to do at home or in a classroom.
    - Focus on physical movement, building, drawing, or role-playing.
    
    Output as a JSON object with an 'activities' key containing a list of strings.
    Example: {{"activities": ["Activity 1", "Activity 2"]}}
    """
    
    data = generate_json(prompt)
    activities = data.get("activities", []) if data else []

    if not activities:
        activities = [
            f"Draw a labelled diagram of {topic}",
            f"Use hand movements to explain {topic}",
            f"Build a simple model related to {topic}",
            f"Teach {topic} to someone using actions",
            f"Act out or role-play concepts related to {topic}",
        ]
        
    if rules.get("repetition") == "high":
        activities.append("Repeat each activity once more to strengthen your memory!")

    return {
        "type": "kinesthetic",
        "topic": topic,
        "activities": activities,
        "rules_applied": rules,
        "source": "gemini-ai"
    }
