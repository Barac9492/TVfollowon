from __future__ import annotations
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class SlackChannelMapping(Base):
    __tablename__ = "slack_channel_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    slack_channel_id = Column(String, nullable=False)
    slack_channel_name = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="slack_channels")


class SlackMessage(Base):
    __tablename__ = "slack_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String, nullable=False, index=True)
    message_ts = Column(String, nullable=False)
    user_name = Column(String)
    text = Column(Text)
    posted_at = Column(DateTime)
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SlackSummary(Base):
    __tablename__ = "slack_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String, nullable=False)
    summary_text = Column(Text, nullable=False)
    message_count = Column(Integer)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
