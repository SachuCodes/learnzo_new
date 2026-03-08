from pydantic import BaseModel, EmailStr, Field
from typing import Literal


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: Literal["student", "teacher"] = "student"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str | None = None
    has_learner: bool | None = None