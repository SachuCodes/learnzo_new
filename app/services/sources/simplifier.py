def simplify_text(text: str, rules: dict) -> str:
    if not text:
        return ""

    simplified = text

    if rules.get("simplify_language"):
        simplified = simplified.replace(",", ".")
        simplified = simplified.replace(";", ".")

    if rules.get("repetition") == "high":
        simplified += "\n\nKey idea: " + simplified.split(".")[0]

    if rules.get("concrete_examples"):
        simplified += "\n\nExample: Think of this like something you see in daily life."

    return simplified
