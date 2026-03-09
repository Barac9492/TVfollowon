from __future__ import annotations
from sqlalchemy import Column, String, Integer, DateTime, Text
from datetime import datetime, timezone
from app.database import Base


class UploadHistory(Base):
    __tablename__ = "upload_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False)
    file_type = Column(String)  # "portfolio" or "comments"
    rows_parsed = Column(Integer, default=0)
    rows_created = Column(Integer, default=0)
    rows_updated = Column(Integer, default=0)
    errors = Column(Text, nullable=True)  # JSON
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
