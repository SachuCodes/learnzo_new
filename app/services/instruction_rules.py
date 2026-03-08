INSTRUCTION_RULES = {

    "adhd": {
        "chunk_size": "small",
        "max_content_length": 450,
        "interaction_frequency": "high",
        "breaks": "frequent",
        "tone": "energetic",
        "preferred_styles": ["K", "V"]
    },

    "autism": {
        "chunk_size": "medium",
        "predictable_structure": True,
        "no_metaphors": True,
        "tone": "calm",
        "preferred_styles": ["V", "R"]
    },

    "dyslexia": {
        "font": "open-dyslexic",
        "text_simplification": True,
        "audio_support": True,
        "preferred_styles": ["A", "V"]
    },

    "dyspraxia": {
        "motor_complexity": "low",
        "step_by_step": True,
        "extra_time": True,
        "preferred_styles": ["V", "A"]
    },

    "dyscalculia": {
        "use_real_world_examples": True,
        "visual_aids": True,
        "stepwise_math": True,
        "preferred_styles": ["V", "K"]
    },

    "apd": {  # Auditory Processing Disorder
        "audio_speed": "slow",
        "captions_required": True,
        "repeat_instructions": True,
        "preferred_styles": ["R", "V"]
    },

    "ocd": {
        "clear_completion_states": True,
        "avoid_open_ended_tasks": True,
        "tone": "reassuring",
        "preferred_styles": ["R"]
    },

    "tourette": {
        "short_sessions": True,
        "low_stimulus": True,
        "flexible_interaction": True,
        "preferred_styles": ["K", "V"]
    },

    "intellectual_disability": {
        "simplified_language": True,
        "repetition": "high",
        "concrete_examples": True,
        "preferred_styles": ["K"]
    },

    "spd": {  # Sensory Processing Disorder
        "low_visual_noise": True,
        "no_flashing": True,
        "gentle_audio": True,
        "preferred_styles": ["R", "A"]
    }
}


def apply_rules(content: dict, rules: dict) -> dict:
    if not rules:
        return content

    text = content.get("text", "")
    if not text:
        return content

    # 1. Smarter truncation (avoid cutting mid-sentence or mid-word)
    max_len = rules.get("max_content_length")
    if max_len and len(text) > max_len:
        truncated = text[:max_len]
        # Try to find a sentence end
        last_period = truncated.rfind('.')
        last_exclamation = truncated.rfind('!')
        last_question = truncated.rfind('?')
        split_at = max(last_period, last_exclamation, last_question)
        
        if split_at > max_len * 0.7:
            text = truncated[:split_at+1]
        else:
            # Fallback to last space to avoid cutting words
            last_space = truncated.rfind(' ')
            if last_space > 0:
                text = truncated[:last_space] + "..."
        content["text"] = text

    # 2. Smarter chunking (avoid cutting mid-word)
    chunk_size_rule = rules.get("chunk_size")
    if chunk_size_rule:
        target_size = 100 if chunk_size_rule == "small" else 250
        words = text.split(' ')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) > target_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1 # +1 for space
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        content["chunks"] = chunks

    return content
