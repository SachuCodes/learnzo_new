import requests
import random
import time

URL_INSTRUCTION = "http://127.0.0.1:8000/instruction/next"
URL_FEEDBACK = "http://127.0.0.1:8000/feedback"

learner_id = "demo_learner"

for step in range(15):
    context = [1, 0.4, random.random(), 0.5, 1]

    res = requests.post(URL_INSTRUCTION, json={
        "learner_id": learner_id,
        "context": context
    }).json()

    instruction = res["instruction"]

    # Simulate learner preference: visual preferred
    reward = 1 if instruction == "visual" else 0

    requests.post(URL_FEEDBACK, json={
        "learner_id": learner_id,
        "reward": reward
    })

    print(f"Step {step+1}: {instruction} → reward {reward}")
    time.sleep(0.5)
