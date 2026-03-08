import requests
import time

BASE_URL = "http://127.0.0.1:8000"

# Fixed learner context
context_vector = [1, 0.72, -0.05, 2, 15]

print("Starting learner simulation...\n")

for step in range(10):
    # Step 1: Ask system for next instruction
    r = requests.post(
        f"{BASE_URL}/instruction/next",
        json={"context_vector": context_vector}
    ).json()

    instruction = r["selected_instruction"]["instruction_type"]
    score = r["selected_instruction"]["ucb_score"]

    # Step 2: Simulate learner preference
    # Learner prefers VISUAL
    reward = 1 if instruction == "visual" else 0

    # Step 3: Send feedback
    requests.post(
        f"{BASE_URL}/feedback",
        json={
            "instruction_type": instruction,
            "reward": reward,
            "context_vector": context_vector
        }
    )

    print(
        f"Step {step+1}: "
        f"Instruction={instruction}, "
        f"Reward={reward}, "
        f"UCB={round(score, 3)}"
    )

    time.sleep(0.5)
