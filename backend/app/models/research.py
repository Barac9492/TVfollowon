from __future__ import annotations
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class ResearchLog(Base):
    __tablename__ = "research_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False, index=True)
    research_type = Column(String, nullable=False)  # "text_extraction" | "web_research"
    input_text = Column(Text, nullable=True)  # For text extraction: the pasted text
    raw_result = Column(Text, nullable=False)  # Full JSON from Claude
    extracted_metrics = Column(Text, nullable=False)  # Parsed structured metrics JSON
    status = Column(String, default="pending")  # "pending" | "approved" | "rejected"
    growth_metrics_id = Column(Integer, ForeignKey("growth_metrics.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    company = relationship("Company")
