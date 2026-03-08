from pydantic import BaseModel
from typing import List

class ContextRequest(BaseModel):
    context_vector: List[float]
