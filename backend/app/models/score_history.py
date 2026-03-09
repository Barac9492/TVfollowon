from __future__ import annotations
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class ScoreHistory(Base):
    __tablename__ = "score_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False, index=True)

    # Score snapshot
    score_value = Column(Integer, nullable=False)
    traffic_score = Column(String, nullable=False)  # green / yellow / red
    score_details = Column(Text, nullable=True)  # Full 6-factor breakdown JSON

    # Change tracking
    previous_score_value = Column(Integer, nullable=True)
    previous_traffic_score = Column(String, nullable=True)
    score_change = Column(Integer, default=0)  # +/- delta

    # Change analysis
    change_reasons = Column(Text, nullable=True)  # JSON: structured reasons for change
    meta_insight = Column(Text, nullable=True)  # Korean summary of what the change means

    # Trigger info
    trigger_type = Column(String, nullable=True)  # "research", "upload", "manual", "initial", "data_clear"
    trigger_detail = Column(String, nullable=True)  # e.g. "web research: 3 new fields"

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="score_history")
