import google.generativeai as genai
import json
import logging
from app.config import GOOGLE_API_KEY

logger = logging.getLogger("learnzo")

def configure_genai():
    if GOOGLE_API_KEY and GOOGLE_API_KEY != "YOUR_GEMINI_API_KEY_HERE" and GOOGLE_API_KEY.strip():
        genai.configure(api_key=GOOGLE_API_KEY)
        return True
    return False

def generate_text(prompt: str, model_name: str = 'gemini-2.5-flash') -> str:
    """Generic text generation with Gemini."""
    if not configure_genai():
        return ""
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        
        # Robust text extraction to avoid "response.text" accessor errors
        if response and response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                text_parts = [part.text for part in candidate.content.parts if hasattr(part, 'text') and part.text]
                if text_parts:
                    return "".join(text_parts).strip()
        
        logger.warning(f"Gemini returned no text parts. Finish reason: {getattr(response.candidates[0], 'finish_reason', 'N/A') if response.candidates else 'No candidates'}")
    except Exception as e:
        logger.error(f"Gemini text generation failed: {str(e)}")
    return ""

def generate_json(prompt: str, model_name: str = 'gemini-2.5-flash') -> any:
    """JSON-based content generation with Gemini."""
    if not configure_genai():
        return None
    
    try:
        model = genai.GenerativeModel(model_name)
        # Ensure the prompt asks for JSON
        if "JSON" not in prompt.upper():
             prompt += "\nOutput the result in strictly valid JSON format."
             
        response = model.generate_content(prompt)
        
        # Extract text safely to avoid "response.text" accessor errors
        text = ""
        if response and response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                text_parts = [part.text for part in candidate.content.parts if hasattr(part, 'text') and part.text]
                if text_parts:
                    text = "".join(text_parts).strip()
        
        if not text:
            logger.warning(f"Gemini JSON generation returned no text. Finish reason: {getattr(response.candidates[0], 'finish_reason', 'N/A') if response.candidates else 'No candidates'}")
            return None
        
        # Extract JSON from markdown if needed
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        else:
             import re
             match = re.search(r'\[.*\]|\{.*\}', text, re.DOTALL)
             if match:
                 text = match.group()
        
        return json.loads(text)
    except Exception as e:
        logger.error(f"Gemini JSON generation failed: {str(e)}")
        return None
