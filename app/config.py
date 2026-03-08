"""
Application configuration.

Prefer environment variables (including via local .env) with safe defaults for dev.
Never hardcode production secrets in code.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def _getenv(name: str, default: str) -> str:
    value = os.getenv(name)
    return default if value is None or value.strip() == "" else value


def _has_env(name: str) -> bool:
    value = os.getenv(name)
    return value is not None and value.strip() != ""


# Database
#
# - If DATABASE_URL is set, use it.
# - Else if any MYSQL_* is set, build a MySQL URL (defaults align with scripts/init_mysql.sql).
# - Else default to local SQLite for a zero-setup dev experience.
_database_url_env = os.getenv("DATABASE_URL")
_mysql_configured = any(
    _has_env(k) for k in ("MYSQL_HOST", "MYSQL_PORT", "MYSQL_DB", "MYSQL_USER", "MYSQL_PASSWORD")
)

MYSQL_HOST = _getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = _getenv("MYSQL_PORT", "3306")
MYSQL_DB = _getenv("MYSQL_DB", "learnzo")
MYSQL_USER = _getenv("MYSQL_USER", "learnzo_user")
MYSQL_PASSWORD = _getenv("MYSQL_PASSWORD", "learnzo_pass")

if _database_url_env and _database_url_env.strip():
    DATABASE_URL = _database_url_env.strip()
elif _mysql_configured:
    DATABASE_URL = (
        f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
else:
    DATABASE_URL = "sqlite:///./learnzo.db"

# Auth (must be overridden in production via env)
SECRET_KEY: str = _getenv(
    "LEARNZO_SECRET_KEY",
    _getenv("SECRET_KEY", "CHANGE_THIS_SECRET_IN_PRODUCTION"),
)
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(_getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Google Gemini API key
GOOGLE_API_KEY = _getenv("GOOGLE_API_KEY", "")

# Allowed disability types for onboarding (exact values)
DISABILITY_TYPES: tuple = (
    "adhd",
    "autism",
    "dyslexia",
    "dyspraxia",
    "dyscalculia",
    "apd",
    "ocd",
    "tourette",
    "intellectual_disability",
    "spd",
)
