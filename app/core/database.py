"""
Compatibility DB module.

The rest of the backend uses a synchronous SQLAlchemy engine/session in `app.db.database`.
This module re-exports the same objects so older imports keep working.
"""

from app.db.database import Base, SessionLocal, engine, get_db  # noqa: F401
