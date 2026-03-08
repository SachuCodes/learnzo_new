from pydantic import BaseModel, Field
from typing import List

class VARKAnswer(BaseModel):
    question_id: int
    answer: str = Field(pattern="^[VARK]$")

class VARKSubmit(BaseModel):
    answers: List[VARKAnswer]
