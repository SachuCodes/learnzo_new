# app/services/strategy_resolver.py

def resolve_instruction_strategy(
    learning_style: str,
    disability_type: str,
    rules: dict
):
    """
    Final decision maker.
    Returns the instruction strategy AFTER applying constraints.
    """

    # Base VARK mapping
    base_strategy = {
        "V": "visual",
        "A": "auditory",
        "R": "reading",
        "K": "kinesthetic"
    }.get(learning_style)

    if not base_strategy:
        raise ValueError("Invalid learning style")

    # Disability-based overrides
    preferred = rules.get("preferred_styles", [])

    # If disability prefers a DIFFERENT style → override
    if preferred:
        # Map preferred VARK to instruction
        vark_to_instruction = {
            "V": "visual",
            "A": "auditory",
            "R": "reading",
            "K": "kinesthetic"
        }

        for p in preferred:
            if vark_to_instruction.get(p):
                return {
                    "final_strategy": vark_to_instruction[p],
                    "reason": f"Disability override: prefers {p}"
                }

    # Default
    return {
        "final_strategy": base_strategy,
        "reason": "Based on VARK assessment"
    }
