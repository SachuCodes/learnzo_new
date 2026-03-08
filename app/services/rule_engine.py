# app/services/rule_engine.py

from app.services.instruction_rules import INSTRUCTION_RULES

ACTIONS = ["visual", "auditory", "reading", "kinesthetic"]

def resolve_learning_strategy(model, context, disability: str | None):
    """
    RL decides instruction.
    Rules only constrain, not override.
    """

    # 1️⃣ RL decides (select_action returns (index, ucb_score))
    action_index, _ucb = model.select_action(context)
    instruction_type = ACTIONS[action_index]

    # 2️⃣ Fetch rules (NO override)
    rules = {}
    if disability:
        rules = INSTRUCTION_RULES.get(disability.lower(), {})

    return instruction_type, rules
