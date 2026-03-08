# app/core/config.py
from __future__ import annotations

from dataclasses import dataclass

from app.config import DATABASE_URL


@dataclass(frozen=True)
class Settings:
    DATABASE_URL: str = DATABASE_URL


settings = Settings()

# ---------- LINUCB ----------
CONTEXT_DIM = 5
ALPHA = 0.5

# ---------- REWARD ENGINE ----------
ENGAGEMENT_INCREASE_REWARD = 1.0
TASK_COMPLETION_REWARD = 1.5
DROPOUT_PENALTY = -1.0
