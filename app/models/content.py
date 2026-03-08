from sqlalchemy import Column, Integer, String, Text, Enum, TIMESTAMP
from app.db.database import Base
import datetime

class Content(Base):
    __tablename__ = "content"

    content_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    learning_style = Column(String(1), nullable=False)
    difficulty = Column(String(10), default="easy")
    content_type = Column(String(20), nullable=False)
    content_data = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
